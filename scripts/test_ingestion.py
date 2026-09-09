"""Smoke test for policy ingestion and chunk metadata."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingestion import process_all_policies


def main() -> None:
    chunks = process_all_policies(str(PROJECT_ROOT / "data" / "company_policy"))
    sources = {chunk["metadata"]["source"] for chunk in chunks}
    expected_sources = {
        "travel_policy_india.txt",
        "travel_policy_us.txt",
        "airport_policy.txt",
        "employee_eligibility.txt",
        "expense_policy.txt",
        "cancellation_policy.txt",
        "approval_policy.txt",
    }
    assert chunks, "No policy chunks were generated."
    assert sources == expected_sources, f"Unexpected policy sources: {sources}"
    assert all(chunk["text"].strip() for chunk in chunks)
    print(f"Ingestion test passed: {len(chunks)} chunks from {len(sources)} sources")


if __name__ == "__main__":
    main()