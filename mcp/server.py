"""MCP server exposing the travel assistant's business tools."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import (
    calculate_reimbursement as _calculate_reimbursement,
    check_employee_eligibility as _check_employee_eligibility,
    validate_trip as _validate_trip,
)

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as error:
    raise RuntimeError(
        "The MCP 2.x SDK is missing. Install the mcp package before starting the server."
    ) from error


mcp = MCPServer("AI Travel Policy Assistant")


@mcp.tool()
def check_employee_eligibility(employee_id: str) -> Dict[str, Any]:
    """Check an employee's travel eligibility by employee ID."""
    return _check_employee_eligibility(employee_id)


@mcp.tool()
def validate_trip(
    employee_id: str,
    trip_type: str,
    amount: float,
    time: str,
) -> Dict[str, Any]:
    """Validate a business trip against employee status and country limits."""
    return _validate_trip(employee_id, trip_type, amount, time)


@mcp.tool()
def calculate_reimbursement(trip_amount: float, policy_limit: float) -> Dict[str, float]:
    """Calculate reimbursable and review amounts for a trip."""
    return _calculate_reimbursement(trip_amount, policy_limit)


if __name__ == "__main__":
    mcp.run("stdio")