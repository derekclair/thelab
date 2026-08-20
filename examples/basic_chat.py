"""Minimal non-interactive example of MemoryChat with Grok + Supermemory."""

import os
from dotenv import load_dotenv

# Make sure we can run from anywhere
load_dotenv()

from thelab_langchain.chat import MemoryChat  # noqa: E402

def main() -> None:
    user_id = os.getenv("DEFAULT_USER_ID", "example-user")

    print(f"Starting MemoryChat for user: {user_id}\n")

    agent = MemoryChat(user_id=user_id)

    # First turn — user introduces themselves
    reply = agent.chat("Hi! My name is Alex and I really love functional programming in Python.")
    print("Assistant:", reply, "\n")

    # Second turn — should recall the preference
    reply = agent.chat("What kind of code style do I prefer?")
    print("Assistant:", reply, "\n")

    print("--- Profile after two turns ---")
    agent.show_profile()


if __name__ == "__main__":
    main()
