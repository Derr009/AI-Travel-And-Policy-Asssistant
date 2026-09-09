"""Smoke test for MCP tool registration and execution."""

from pathlib import Path
import asyncio
import importlib.util
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import calculate_reimbursement, check_employee_eligibility, validate_trip


def load_mcp_server():
    module_path = PROJECT_ROOT / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("travel_mcp_server", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


async def main() -> None:
    mcp_module = load_mcp_server()
    tools = {
        tool.name for tool in await mcp_module.mcp.list_tools()
    }
    assert tools == {
        "check_employee_eligibility",
        "validate_trip",
        "calculate_reimbursement",
    }
    assert check_employee_eligibility("EMP001")["status"] == "Eligible"
    assert validate_trip("EMP001", "Airport", 2500, "22:30")["status"] == "Needs Approval"
    assert calculate_reimbursement(2500, 2000)["reimbursable_amount"] == 2000
    print(f"MCP test passed: {', '.join(sorted(tools))}")


if __name__ == "__main__":
    asyncio.run(main())