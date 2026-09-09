"""Smoke test for embedding-based policy retrieval."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag import PolicyRAG


def main() -> None:
    rag = PolicyRAG.from_policy_directory(PROJECT_ROOT / "data" / "company_policy")
    results = rag.search_policy("What is the airport travel limit in India?", top_k=3)
    assert results, "Retrieval returned no results."
    assert results[0]["metadata"]["source"] in {
        "airport_policy.txt",
        "travel_policy_india.txt",
    }, f"Unexpected top result: {results[0]['metadata']['source']}"
    assert all("score" in result for result in results)
    print("Retrieval test passed")
    for result in results:
        print(f"- {result['metadata']['source']}: {result['score']:.4f}")


if __name__ == "__main__":
    main()