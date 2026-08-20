"""
VoiceOrchestrator - Bridges audio (via NVIDIA Riva) with the LangGraph agent brain.

This is the core of the voice experience. It manages:
- Listening for user speech (ASR)
- Sending transcribed text to the agent
- Receiving responses and synthesizing speech (TTS)
- Handling interruptions (barge-in)
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from thelab_langchain.agent.graph import get_agent  # type: ignore

from .audio import AudioConfig, play_audio, record_until_silence
from .riva import get_riva_clients


class VoiceOrchestrator:
    """
    High-level coordinator for voice conversations.

    Phase 1 (MVP) implementation:
    - Record until silence (energy VAD)
    - Transcribe with Riva ASR
    - Call the agent brain
    - Synthesize response with Riva TTS
    - Play audio

    Phase 2 will upgrade this to true streaming + barge-in.
    """

    def __init__(
        self,
        user_id: str = "default",
        thread_id: str = "default",
        agent: Callable[[str], str] | None = None,
        riva_uri: str | None = None,
    ):
        self.user_id = user_id
        self.thread_id = thread_id

        # Prefer the real LangGraph agent if none is passed in
        if agent is None:
            try:
                compiled_graph = get_agent(user_id=self.user_id)
                self.agent = lambda text: self._call_langgraph_agent(text, compiled_graph)
            except Exception:
                self.agent = self._default_agent
        else:
            self.agent = agent

        # Riva clients (can point to local Riva server on DGX Spark)
        self.asr, self.tts = get_riva_clients(uri=riva_uri)

        self.audio_config = AudioConfig()
        self._running = False

        # Benchmark instrumentation (enabled when BENCHMARK_MODE=1 or BENCHMARK_REPORT_DIR is set)
        self._benchmark_mode = bool(os.getenv("BENCHMARK_MODE") or os.getenv("BENCHMARK_REPORT_DIR"))
        self._benchmark_report_dir: Path | None = None
        if self._benchmark_mode:
            report_dir = os.getenv("BENCHMARK_REPORT_DIR")
            if report_dir:
                self._benchmark_report_dir = Path(report_dir)
                self._benchmark_report_dir.mkdir(parents=True, exist_ok=True)

    def _emit_benchmark_event(self, event: dict[str, Any]) -> None:
        """Emit a structured timing / measurement event (no-op unless benchmark mode)."""
        if not self._benchmark_mode:
            return

        event = {"ts": time.time(), "type": event.get("type", "event"), **event}

        # Always print a machine-readable line (easy to capture in baseline runs)
        print(f"[BENCHMARK] {json.dumps(event, default=str)}")

        # If a report dir was provided, append to events.jsonl there as well
        if self._benchmark_report_dir:
            events_file = self._benchmark_report_dir / "events.jsonl"
            with events_file.open("a") as f:
                f.write(json.dumps(event, default=str) + "\n")

    def _default_agent(self, text: str) -> str:
        """Very basic fallback (used only if the real graph fails to load)."""
        return f"You said: {text}. (Using fallback agent — real LangGraph brain not wired yet.)"

    def _call_langgraph_agent(self, text: str, graph) -> str:
        """Call the compiled LangGraph and extract the final response."""
        try:
            # Pass a proper HumanMessage so the graph state stays clean
            result = graph.invoke({
                "messages": [HumanMessage(content=text)],
                "user_id": self.user_id,
                "thread_id": self.thread_id,
            })

            if isinstance(result, dict) and "messages" in result:
                last_msg = result["messages"][-1]
                if hasattr(last_msg, "content"):
                    return last_msg.content
                return str(last_msg)
            return str(result)
        except Exception as e:
            return f"[Agent error] {e}"

    async def start_voice_session(self) -> None:
        """Run the main voice conversation loop until stopped."""
        print("[Voice] Starting voice session (MVP non-streaming mode)")
        print(f"[Voice] User: {self.user_id} | Thread: {self.thread_id}")
        print("[Voice] Say something... (Ctrl+C to stop)")

        self._running = True

        try:
            while self._running:
                # 1. Listen (end of speech = VAD trigger)
                eos_start = time.time()
                audio = record_until_silence(self.audio_config)
                eos_end = time.time()

                if len(audio) < self.audio_config.sample_rate * 0.3:
                    # Too short, probably noise — ignore
                    continue

                self._emit_benchmark_event({
                    "type": "end_of_speech",
                    "duration_s": round(eos_end - eos_start, 3),
                    "audio_length_s": round(len(audio) / self.audio_config.sample_rate, 2),
                })

                # 2. Transcribe
                t0 = time.time()
                transcript = self.asr.recognize(audio, self.audio_config.sample_rate)
                t1 = time.time()

                if not transcript:
                    print("[Voice] (no speech detected)")
                    continue

                print(f"\n[You] {transcript}")

                self._emit_benchmark_event({
                    "type": "transcript_ready",
                    "asr_latency_s": round(t1 - t0, 3),
                    "transcript_len": len(transcript),
                })

                # 3. Call the agent brain
                t0 = time.time()
                response_text = self.agent(transcript)
                t1 = time.time()

                print(f"[Agent] {response_text}")

                self._emit_benchmark_event({
                    "type": "response_ready",
                    "agent_latency_s": round(t1 - t0, 3),
                    "response_len": len(response_text or ""),
                })

                # 4. Synthesize + play (first audio out approximation)
                t0 = time.time()
                tts_audio = self.tts.synthesize(
                    response_text,
                    sample_rate=22050,  # Common for many NeMo TTS voices
                )
                t1 = time.time()

                play_start = time.time()
                play_audio(tts_audio, sample_rate=22050)
                play_end = time.time()

                self._emit_benchmark_event({
                    "type": "first_audio_out",
                    "tts_latency_s": round(t1 - t0, 3),
                    "playback_duration_s": round(play_end - play_start, 3),
                    "total_turn_latency_s": round(play_start - eos_end, 3),  # rough end-to-end voice turn
                })

        except KeyboardInterrupt:
            print("\n[Voice] Session interrupted by user")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the voice session."""
        self._running = False
        print("[Voice] Session ended")

    # --- Future hooks for streaming / barge-in (Phase 2) ---

    async def _listen_streaming(self):
        """Placeholder for true streaming ASR."""
        raise NotImplementedError("Coming in Phase 2")

    async def _speak_streaming(self, text: str):
        """Placeholder for streaming TTS (start speaking before full response)."""
        raise NotImplementedError("Coming in Phase 2")
