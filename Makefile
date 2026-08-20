# thelab-langchain — Makefile
# All development happens inside a project-local venv to avoid dependency hell.
# Never use global pip / homebrew python for this project.
#
# For the voice spike / Lenovo Go prototype:
#   Just run `make` (bare) in this directory.
#   It preps the venv + package so the sibling conversational-voice-agent spike can use the real agent.
#
# Then (in the other shell): clone github.com/derekclair/conversational-voice-agent
#   next to this repo and: cd ../conversational-voice-agent && make
#   (bare `make` there starts the voice loop that drives this agent.)
#
# Use `make help` for the full list of targets (chat, local, install, pids, kill, etc.).

SHELL := /bin/bash
.DEFAULT_GOAL := local

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
CLI := $(VENV)/bin/thelab-chat

.PHONY: help venv install run chat profile env lint clean local pids stop kill reset

help:
	@echo "thelab-langchain — venv-first development"
	@echo ""
	@echo "For the Lenovo Go voice spike (the 'two shells' flow):"
	@echo "  Bare 'make' (or 'make local')  → prep this side so the sibling conversational-voice-agent can drive the *real* agent + Supermemory"
	@echo "  Then (other shell): cd ../conversational-voice-agent && make keys && make"
	@echo ""
	@echo "Normal development targets:"
	@echo "  make install     Create .venv + install the package + dev tools (recommended first step)"
	@echo "  make run / chat  Interactive chat with the agent (uses venv directly)"
	@echo "  make profile     Show Supermemory profile for the default user"
	@echo "  make env         Print current resolved config (keys redacted)"
	@echo "  make lint        Run ruff + mypy"
	@echo "  make clean       Remove venv + caches"
	@echo ""
	@echo "Cleanup (cross-repo aware):"
	@echo "  make pids        List thelab + spike processes + pipes"
	@echo "  make stop        Graceful SIGTERM"
	@echo "  make kill        Force kill (thelab + local_tts bits)"
	@echo "  make reset       stop + pipe cleanup (spike artifacts)"
	@echo ""
	@echo "See the 'local' target output for the exact next steps and key requirements."

# Create or refresh the project venv and install the package + dev tools.
# This is the only supported way to work on this project.
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: pyproject.toml
	@echo "==> Creating isolated venv at $(VENV) (no global pollution)"
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip wheel
	$(PIP) install -e ".[dev]"
	@echo ""
	@echo "==> Venv ready. To activate in your shell:"
	@echo "    source $(VENV)/bin/activate"
	@echo "    (or just keep using 'make run' / 'make chat' — they use the venv directly)"
	@touch $(VENV)/bin/activate

install: venv
	@echo "==> Install complete. Use 'make run' or 'make chat' to start."

# Prep this side for the conversational-voice-agent Lenovo Go voice spike (the "two shells" flow).
# - Ensures this project's venv + editable package exist (so `pip install -e ../thelab`
#   from the sibling conversational-voice-agent/.venv will succeed cleanly and pull the right code/deps).
# - The actual cross wiring + key symlink + running the voice waiter happens in the
#   *conversational-voice-agent* dir via `cd conversational-voice-agent && make local` (or make demo).
# - This target is intentionally lightweight: just make sure the thelab package is
#   installable from the sibling spike shell.
local: install
	@echo "==> thelab prepped for the voice spike (you just ran 'make' here)."
	@echo ""
	@echo "    Next step (other shell / other repo):"
	@echo "      cd ../conversational-voice-agent"
	@echo "      cp .env.example .env           # add your keys here"
	@echo "      make keys                      # imports XAI_API_KEY + SUPERMEMORY_API_KEY into thelab/.env"
	@echo "      make                           # (or make demo for the quickest real-agent + speak test)"
	@echo ""
	@echo "    The conversational-voice-agent Makefile will symlink thelab/.env if present so load_dotenv() works."
	@echo "    Once the voice loop waiter is running:"
	@echo "      echo 'start' > /tmp/voice_trigger"
	@echo "    Or run the physical Teams button listener in a third shell."
	@echo ""
	@echo "    Watch the conversational-voice-agent terminal for real [Parakeet] Partial lines + real [AGENT] success."
	@echo ""

# All the useful targets depend on the venv existing.
run: $(CLI)
	$(CLI) chat

chat: $(CLI)
	$(CLI) chat

profile: $(CLI)
	$(CLI) profile

env: $(CLI)
	$(CLI) env

lint: $(PYTHON)
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy src

clean:
	@echo "==> Removing venv and Python caches"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(VENV)
	@echo "==> Clean. Run 'make install' to recreate."

# --- Docker / DigitalOcean Registry targets ---

REGISTRY ?= registry.digitalocean.com/basementlab
IMAGE    ?= $(REGISTRY)/thelab-agent
TAG      ?= latest

docker-build:
	@echo "==> Building $(IMAGE):$(TAG)"
	docker build -t $(IMAGE):$(TAG) .

docker-push: docker-build
	@echo "==> Pushing $(IMAGE):$(TAG) to DigitalOcean Container Registry"
	docker push $(IMAGE):$(TAG)

docker-run-dgx:
	@echo "==> Running agent on DGX using image from registry"
	REGISTRY=$(REGISTRY) TAG=$(TAG) docker compose up agent

docker-login:
	doctl registry login

.PHONY: docker-build docker-push docker-run-dgx docker-login

# --- Benchmark harness (Feature 007) ---

BENCH := $(VENV)/bin/python -m benchmarks.runner

.PHONY: benchmark benchmark-short benchmark-dry

benchmark: $(PYTHON)
	@echo "==> Running benchmark (short scenario by default). Use BENCHMARK_REPORT_DIR or the runner directly for full control."
	$(BENCH) run --scenario short

benchmark-short: benchmark

benchmark-dry: $(PYTHON)
	$(BENCH) run --scenario short --dry-run

benchmark-help: $(PYTHON)
	$(BENCH) --help

# --- Process cleanup helpers (rogue PIDs from chat, voice, spike cross-talk, etc.) ---
# These are safe no-ops if nothing matches. Useful when you have multiple shells
# running make chat / voice_loop bits / button listeners across the two repos.

pids status:
	@echo "==> thelab-related processes:"
	@pgrep -af 'thelab-chat|thelab_langchain|benchmarks\.runner' | grep -v 'pgrep -af' || echo "  (none)"
	@pgrep -af 'local_tts\.(voice_loop|button_listener)' | grep -v 'pgrep -af' || echo "  (no cross-repo conversational-voice-agent spike processes)"
	@echo ""
	@echo "==> Local voice pipes (if this shell has been used for spike triggers):"
	@ls -l /tmp/voice_trigger /tmp/voice_speak 2>/dev/null || echo "  (no voice pipes)"

stop:
	@echo "==> Stopping thelab / spike processes (SIGTERM)..."
	@pkill -f 'thelab-chat' 2>/dev/null || true
	@pkill -f 'thelab_langchain.*(cli|voice)' 2>/dev/null || true
	@pkill -f 'local_tts\.(voice_loop|button_listener)' 2>/dev/null || true
	@echo "==> SIGTERM sent. Check with 'make pids'."

kill:
	@echo "==> Force-killing rogue thelab/spike PIDs..."
	@pkill -9 -f 'thelab-chat' 2>/dev/null || true
	@pkill -9 -f 'thelab_langchain' 2>/dev/null || true
	@pkill -9 -f 'local_tts\.(voice_loop|button_listener)' 2>/dev/null || true
	@echo "==> Force kill done."

reset: stop
	@echo "==> Also cleaning voice pipes (spike artifacts)..."
	@rm -f /tmp/voice_trigger /tmp/voice_speak 2>/dev/null || true
	@echo "==> Reset complete. cd ../conversational-voice-agent && make reset (or make audio-reset) if you also need audio cleanup."
	@echo "    Then 'make local' (or bare 'make') in the appropriate repo to restart."
