"""Smoke test for persistent two-turn conversation handling."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from conversation_service import ConversationService


def main() -> None:
    service = ConversationService.from_policy_directory(PROJECT_ROOT / "data" / "company_policy")
    conversation_id = service.create_conversation(user_id="EMP001")

    first = service.ask(conversation_id, "Can I take an airport trip?", employee_id="EMP001")
    assert first["state"]["trip_type"] == "Airport"

    second = service.ask(conversation_id, "What if it costs INR 2,500?")
    assert second["state"]["employee_id"] == "EMP001"
    assert second["tool_results"]["validation"]["status"] == "Needs Approval"
    assert len(second["messages"]) == 4
    print("Conversation service test passed: follow-up resolved from stored state")


if __name__ == "__main__":
    main()