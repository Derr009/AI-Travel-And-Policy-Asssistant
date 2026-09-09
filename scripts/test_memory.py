"""Smoke test for PostgreSQL conversation memory."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from memory import ConversationMemory


def main() -> None:
    memory = ConversationMemory(recent_message_limit=6)
    conversation_id = memory.create_conversation(user_id="EMP001")
    memory.add_message(conversation_id, "user", "What is the India travel limit?")
    memory.add_message(conversation_id, "assistant", "The standard limit is INR 2,000.")
    memory.update_state(conversation_id, {"employee_id": "EMP001", "country": "India"})

    messages = memory.get_recent_messages(conversation_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert memory.get_state(conversation_id)["employee_id"] == "EMP001"
    print(f"Memory test passed for conversation {conversation_id}")


if __name__ == "__main__":
    main()