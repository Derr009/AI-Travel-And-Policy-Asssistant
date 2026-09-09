"""Interactive terminal client for the travel-policy assistant."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from conversation_service import ConversationService


def main() -> None:
    service = ConversationService.from_policy_directory(
        PROJECT_ROOT / "data" / "company_policy"
    )
    employee_id = input("Employee ID (optional): ").strip() or None
    conversation_id = service.create_conversation(user_id=employee_id)
    print(f"Conversation: {conversation_id}")
    print("Type a question. Enter 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not question:
            print("Please enter a question.")
            continue

        try:
            result = service.ask(conversation_id, question, employee_id=employee_id)
            print(f"Assistant: {result['answer']}")
            print(f"Route: {result['route']}")
            if result.get("sources"):
                print(f"Sources: {', '.join(result['sources'])}")
            print()
        except Exception as error:
            print(f"Assistant error: {error}\n")


if __name__ == "__main__":
    main()