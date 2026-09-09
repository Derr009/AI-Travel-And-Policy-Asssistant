"""Smoke tests for the database-backed travel tools."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import calculate_reimbursement, check_employee_eligibility, validate_trip


def main() -> None:
    eligibility = check_employee_eligibility("EMP001")
    assert eligibility["status"] == "Eligible"
    assert eligibility["country"] == "India"
    assert eligibility["is_eligible"] is True

    validation = validate_trip("EMP001", "Airport", 2500, "22:30")
    assert validation["status"] == "Needs Approval"
    assert len(validation["reasons"]) == 2

    reimbursement = calculate_reimbursement(2500, 2000)
    assert reimbursement["reimbursable_amount"] == 2000
    assert reimbursement["amount_requiring_review"] == 500

    assert check_employee_eligibility("EMP006")["status"] == "Approval Required"
    assert validate_trip("EMP006", "Airport", 50, "12:00")["status"] == "Needs Approval"
    assert check_employee_eligibility("UNKNOWN")["status"] == "Not Found"
    print("Tools test passed: database, eligibility, validation, reimbursement")


if __name__ == "__main__":
    main()