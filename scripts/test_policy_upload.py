"""Smoke test for upload validation and live RAG reload."""

from io import BytesIO
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.app import create_app


class FakeMemory:
    def list_conversations(self, user_id):
        return []


class FakeRAG:
    def reload_from_policy_directory(self, policy_directory):
        return 2


class FakeAssistant:
    rag = FakeRAG()


class FakeService:
    assistant = FakeAssistant()
    memory = FakeMemory()


def main() -> None:
    client = create_app(FakeService()).test_client()
    response = client.post(
        "/policies/upload",
        data={"file": (BytesIO(b"New policy: rental cars require approval."), "rental_policy.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    assert response.get_json()["source"] == "rental_policy.txt"
    assert response.get_json()["status"] == "pending_review"
    assert client.post(
        "/policies/upload",
        data={"file": (BytesIO(b"not text"), "policy.pdf")},
        content_type="multipart/form-data",
    ).status_code == 400
    print("Policy upload test passed")


if __name__ == "__main__":
    main()