"""End-to-end MCP stdio client test."""

from __future__ import annotations

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    server = StdioServerParameters(
        command=str(PROJECT_ROOT / "venv" / "bin" / "python"),
        args=[str(PROJECT_ROOT / "mcp" / "server.py")],
        cwd=PROJECT_ROOT,
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            expected = {
                "check_employee_eligibility",
                "validate_trip",
                "calculate_reimbursement",
            }
            assert tool_names == expected

            eligibility = await session.call_tool(
                "check_employee_eligibility", {"employee_id": "EMP001"}
            )
            validation = await session.call_tool(
                "validate_trip",
                {
                    "employee_id": "EMP001",
                    "trip_type": "Airport",
                    "amount": 2500,
                    "time": "22:30",
                },
            )
            reimbursement = await session.call_tool(
                "calculate_reimbursement",
                {"trip_amount": 2500, "policy_limit": 2000},
            )

            eligibility_data = eligibility.structured_content["result"]
            validation_data = validation.structured_content["result"]
            reimbursement_data = reimbursement.structured_content["result"]
            assert eligibility_data["status"] == "Eligible"
            assert validation_data["status"] == "Needs Approval"
            assert reimbursement_data["reimbursable_amount"] == 2000
            print(f"Discovered tools: {', '.join(sorted(tool_names))}")
            print("Eligibility:", eligibility_data)
            print("Validation:", validation_data)
            print("Reimbursement:", reimbursement_data)
            print("MCP client test passed")


if __name__ == "__main__":
    asyncio.run(main())