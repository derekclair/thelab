"""
Minimal example that follows the official Supermemory "next steps" guide exactly,
but using Grok (xAI) via langchain-xai instead of OpenAI.

See: https://supermemory.ai/docs/integrations/langchain

This proves that Supermemory is LLM-agnostic — you can (and should) use it with
whatever chat model you prefer.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- The only two changes from the official guide snippet ---
from langchain_xai import ChatXAI          # instead of langchain_openai.ChatOpenAI
from supermemory import Supermemory

memory = Supermemory()
llm = ChatXAI(model=os.getenv("LLM_MODEL", "grok-3"))
# ------------------------------------------------------------

# Retrieve context (exactly as shown in the guide)
result = memory.profile(container_tag="user-123", q="preferences")
context = result.profile.static or []

print("=== Supermemory returned context ===")
print(context or "(no static facts yet)")
print()

# Use in chain (using the modern LangChain message format)
# NOTE: assign the joined string to a variable first — a backslash inside an
# f-string expression is a SyntaxError on Python < 3.12 (our minimum is 3.11).
context_lines = "\n".join(context)
response = llm.invoke([
    {"role": "system", "content": f"User context:\n{context_lines}"},
    {"role": "user", "content": "Help me with my project"},
])

print("=== LLM response ===")
print(response.content)
