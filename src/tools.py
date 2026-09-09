"""Deterministic employee, trip-validation, and reimbursement tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from database import find_employee


POLICY_LIMITS = {"India": 2000.0, "United States": 75.0}


def check_employee_eligibility(employee_id: str) -> Dict[str, Any]:
    employee = find_employee(employee_id)
    if employee is None:
        return {"status": "Not Found", "employee_id": employee_id}
    return {
        "status": employee["eligibility_status"],
        "employee_id": employee["employee_id"],
        "country": employee["country"],
        "employee_type": employee["employee_type"],
        "is_eligible": employee["is_eligible"],
    }


def validate_trip(
    employee_id: str,
    trip_type: str,
    amount: float,
    time: str,
) -> Dict[str, Any]:
    employee = find_employee(employee_id)
    if employee is None:
        return {"status": "Not Found", "reason": f"Employee {employee_id} does not exist."}
    if amount < 0:
        raise ValueError("Trip amount cannot be negative.")
    try:
        trip_time = datetime.strptime(time, "%H:%M").time()
    except ValueError as error:
        raise ValueError("Time must use HH:MM format.") from error

    limit = POLICY_LIMITS.get(employee["country"])
    if employee["eligibility_status"] == "Not Eligible":
        return {"status": "Not Eligible", "reason": "Employee is not eligible for business travel."}
    if employee["eligibility_status"] == "Approval Required":
        return {"status": "Needs Approval", "reason": "Employee travel eligibility requires approval."}
    if limit is None:
        return {"status": "Needs Review", "reason": "No policy limit is configured for this country."}

    late_night = trip_time >= datetime.strptime("22:00", "%H:%M").time() or trip_time < datetime.strptime("06:00", "%H:%M").time()
    reasons = []
    if amount > limit:
        reasons.append(f"The trip exceeds the standard {employee['country']} limit of {limit:g}.")
    if late_night:
        reasons.append("Late-night business travel may require additional approval.")
    return {
        "status": "Needs Approval" if reasons else "Approved",
        "employee_id": employee["employee_id"],
        "trip_type": trip_type,
        "amount": amount,
        "policy_limit": limit,
        "reasons": reasons,
    }


def calculate_reimbursement(trip_amount: float, policy_limit: float) -> Dict[str, float]:
    if trip_amount < 0 or policy_limit < 0:
        raise ValueError("Amounts cannot be negative.")
    reimbursable = min(trip_amount, policy_limit)
    return {
        "trip_amount": trip_amount,
        "policy_limit": policy_limit,
        "reimbursable_amount": reimbursable,
        "amount_requiring_review": max(trip_amount - policy_limit, 0.0),
    }