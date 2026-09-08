"""
Ingestion & Preprocessing Module
Reads, cleans, tags metadata, and chunks company policy text files.
Designed for import into downstream Vector Store / RAG pipelines.
"""

import os
import re
from typing import List, Dict, Any

# Standardized metadata tags based on policy filenames
METADATA_RULES: Dict[str, Dict[str, str]] = {
    "travel_policy_india.txt": {"policy_type": "travel", "country": "India"},
    "travel_policy_us.txt": {"policy_type": "travel", "country": "US"},
    "airport_policy.txt": {"policy_type": "airport", "country": "Global"},
    "employee_eligibility.txt": {"policy_type": "eligibility", "country": "Global"},
    "expense_policy.txt": {"policy_type": "expense", "country": "Global"},
    "cancellation_policy.txt": {"policy_type": "cancellation", "country": "Global"},
    "approval_policy.txt": {"policy_type": "approval", "country": "Global"}
}


def load_raw_documents(policy_dir: str) -> Dict[str, str]:
    """Reads all .txt files from the designated directory."""
    raw_docs = {}
    if not os.path.exists(policy_dir):
        raise FileNotFoundError(f"Policy directory not found at: {policy_dir}")

    for filename in os.listdir(policy_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(policy_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                raw_docs[filename] = f.read()
    return raw_docs


def clean_text(text: str) -> str:
    """Normalizes whitespace while preserving section breaks and structure."""
    if not text or not text.strip():
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def chunk_document(
    text: str, 
    source_filename: str, 
    chunk_size: int = 400, 
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """Splits text into sliding-window chunks with metadata for vector embedding."""
    cleaned_content = clean_text(text)
    if not cleaned_content:
        return []

    chunks = []
    start = 0
    doc_length = len(cleaned_content)

    base_metadata = METADATA_RULES.get(
        source_filename, 
        {"policy_type": "general", "country": "Global"}
    )

    chunk_id = 0
    while start < doc_length:
        end = start + chunk_size
        chunk_text = cleaned_content[start:end]

        chunk_data = {
            "chunk_id": f"{source_filename}_chunk_{chunk_id}",
            "text": chunk_text,
            "metadata": {
                "source": source_filename,
                **base_metadata
            }
        }
        chunks.append(chunk_data)
        start += (chunk_size - chunk_overlap)
        chunk_id += 1

    return chunks


def process_all_policies(policy_dir: str) -> List[Dict[str, Any]]:
    """Pipeline runner exposed for external modules (e.g., embeddings/vector DB creation)."""
    raw_docs = load_raw_documents(policy_dir)
    all_chunks = []

    for filename, content in raw_docs.items():
        doc_chunks = chunk_document(content, filename)
        all_chunks.extend(doc_chunks)

    return all_chunks


if __name__ == "__main__":
    # Internal developer verification script when running this file directly
    policy_path = os.path.join("data", "company_policy")
    processed = process_all_policies(policy_path)
    print(f"Ingestion Module Test: Successfully generated {len(processed)} chunks.")