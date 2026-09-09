"""Smoke tests for agent routing and combined tool workflow."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent import TravelAssistant


def main() -> None:
    assistant = TravelAssistant.from_policy_directory(PROJECT_ROOT / "data" / "company_policy")

    policy = assistant.answer("What is the standard travel limit in India?")
    print("\nPolicy answer:\n", policy["answer"])
    assert policy["route"] == "rag"
    assert policy["sources"]

    eligibility = assistant.answer("Is EMP001 eligible for business travel?")
    print("\nEligibility answer:\n", eligibility["answer"])
    assert eligibility["route"] == "tool"
    assert "eligible" in eligibility["answer"].lower()

    trip = assistant.answer("Can EMP001 take an airport trip costing INR 2,500?")
    print("\nTrip answer:\n", trip["answer"])
    assert trip["route"] == "tool+rag"
    assert trip["tool_results"]["validation"]["status"] == "Needs Approval"
    assert trip["tool_results"]["reimbursement"]["reimbursable_amount"] == 2000

    print("Agent test passed: RAG, eligibility tool, and combined trip workflow")


if __name__ == "__main__":
    main()