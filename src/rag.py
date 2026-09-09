"""Policy retrieval and context preparation for the RAG pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

from embeddings import PolicyVectorStore
from ingestion import process_all_policies


class PolicyRAG:
    """Retrieves policy evidence and optionally passes it to an LLM callable."""

    def __init__(self, store: PolicyVectorStore) -> None:
        self.store = store

    @classmethod
    def from_policy_directory(cls, policy_dir: str | Path) -> "PolicyRAG":
        return cls(PolicyVectorStore(chunks=process_all_policies(str(policy_dir))))

    def search_policy(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.store.search(query, top_k=top_k)

    def build_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        results = self.search_policy(query, top_k=top_k)
        return {
            "query": query,
            "results": results,
            "sources": sorted({item["metadata"]["source"] for item in results}),
        }

    def answer(
        self,
        query: str,
        llm: Callable[[str], str],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        context = self.build_context(query, top_k=top_k)
        if not context["results"]:
            return {
                "answer": "I could not find information about that in the available policy documents.",
                "sources": [],
                "results": [],
            }
        prompt = (
            "Answer only from the policy context below. If the answer is not supported, "
            "say that the information is unavailable. Cite the relevant source filename.\n\n"
            f"Question: {query}\n\n"
            "Policy context:\n"
            + "\n\n".join(
                f"Source: {item['metadata']['source']}\n{item['text']}"
                for item in context["results"]
            )
        )
        return {
            "answer": llm(prompt),
            "sources": context["sources"],
            "results": context["results"],
        }