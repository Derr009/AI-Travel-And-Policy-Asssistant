"""Embedding and FAISS vector-store utilities for policy chunks."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_MODEL_NAME = "nomic-embed-text"
DEFAULT_MIN_SCORE = 0.70


def _load_dependencies():
    try:
        import faiss
        from langchain_ollama import OllamaEmbeddings
    except ImportError as error:
        raise RuntimeError(
            "Day 2 dependencies are missing. Install requirements.txt in the project venv."
        ) from error
    return faiss, OllamaEmbeddings


class PolicyVectorStore:
    """In-memory policy vector store with optional FAISS persistence."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        chunks: Iterable[Dict[str, Any]] | None = None,
    ) -> None:
        _, ollama_embeddings = _load_dependencies()
        self.model_name = model_name
        self.model = ollama_embeddings(model=model_name)
        self.chunks: List[Dict[str, Any]] = list(chunks or [])
        self.index = None
        if self.chunks:
            self.build(self.chunks)

    def build(self, chunks: Iterable[Dict[str, Any]]) -> None:
        faiss, _ = _load_dependencies()
        self.chunks = list(chunks)
        if not self.chunks:
            raise ValueError("Cannot build a vector store from zero chunks.")
        vectors = self.model.embed_documents([chunk["text"] for chunk in self.chunks])
        vectors = self._normalize_vectors(vectors)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("Query must not be empty.")
        if self.index is None:
            raise ValueError("Vector store has not been built.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1.")

        query_vector = self._normalize_vectors([self.model.embed_query(query)])
        scores, positions = self.index.search(query_vector, min(top_k, len(self.chunks)))
        results = []
        for score, position in zip(scores[0], positions[0]):
            if position < 0:
                continue
            if float(score) < min_score:
                continue
            result = dict(self.chunks[position])
            result["score"] = float(score)
            results.append(result)
        return results

    @staticmethod
    def _normalize_vectors(vectors):
        import numpy as np

        vectors = np.asarray(vectors, dtype="float32")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)

    def save(self, directory: str | Path) -> None:
        faiss, _ = _load_dependencies()
        if self.index is None:
            raise ValueError("Vector store has not been built.")
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(target / "policies.index"))
        with (target / "chunks.pkl").open("wb") as file:
            pickle.dump({"model_name": self.model_name, "chunks": self.chunks}, file)

    @classmethod
    def load(cls, directory: str | Path) -> "PolicyVectorStore":
        faiss, _ = _load_dependencies()
        target = Path(directory)
        with (target / "chunks.pkl").open("rb") as file:
            payload = pickle.load(file)
        store = cls(model_name=payload["model_name"])
        store.chunks = payload["chunks"]
        store.index = faiss.read_index(str(target / "policies.index"))
        return store