"""Backend acceptance scenarios for the travel-policy assistant."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent import TravelAssistant
from rag import PolicyRAG
from tools import calculate_reimbursement, check_employee_eligibility, validate_trip


def main() -> None:
    assistant = TravelAssistant(
        PolicyRAG.from_policy_directory(PROJECT_ROOT / "data" / "company_policy")
    )
    passed = 0

    policy_questions = [
        "What is the standard travel limit in India?",
        "What is the standard travel limit in the US?",
        "Are airport trips allowed?",
        "Are late-night trips allowed?",
        "What information is required for an expense?",
    ]
    for question in policy_questions:
        result = assistant.answer(question)
        assert result["route"] == "rag" and result["sources"]
        passed += 1

    eligibility_cases = {
        "EMP001": "Eligible",
        "EMP002": "Approval Required",
        "EMP004": "Not Eligible",
    }
    for employee_id, expected_status in eligibility_cases.items():
        result = check_employee_eligibility(employee_id)
        assert result["status"] == expected_status
        passed += 1
    assert check_employee_eligibility("UNKNOWN")["status"] == "Not Found"
    passed += 1

    validation_cases = [
        ("EMP001", "Airport", 1500, "12:00", "Approved"),
        ("EMP001", "Airport", 2500, "12:00", "Needs Approval"),
        ("EMP003", "Airport", 50, "12:00", "Approved"),
        ("EMP003", "Airport", 100, "12:00", "Needs Approval"),
    ]
    for employee_id, trip_type, amount, trip_time, expected_status in validation_cases:
        assert validate_trip(employee_id, trip_type, amount, trip_time)["status"] == expected_status
        passed += 1

    reimbursement = calculate_reimbursement(2500, 2000)
    assert reimbursement["reimbursable_amount"] == 2000
    assert reimbursement["amount_requiring_review"] == 500
    passed += 1

    for question in (
        "Does the company reimburse hotel bookings?",
        "What is the maximum flight ticket price?",
        "Can I book a rental car?",
    ):
        result = assistant.answer(question)
        assert result["sources"] == []
        assert "could not find" in result["answer"].lower()
        passed += 1

    try:
        assistant.answer("")
    except ValueError:
        passed += 1
    else:
        raise AssertionError("Empty questions must fail clearly.")

    try:
        validate_trip("EMP001", "Airport", -1, "12:00")
    except ValueError:
        passed += 1
    else:
        raise AssertionError("Negative amounts must fail clearly.")

    print(f"Scenario tests passed: {passed} cases")


if __name__ == "__main__":
    main()