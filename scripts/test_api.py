"""Smoke test for the backend Flask API without starting a server."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import create_app


class FakeMemory:
    def __init__(self):
        self.messages = []

    def get_recent_messages(self, conversation_id):
        return self.messages

    def delete_conversation(self, conversation_id):
        self.messages.clear()


class FakeService:
    def __init__(self):
        self.memory = FakeMemory()

    def create_conversation(self, user_id=None):
        return "test-conversation"

    def ask(self, conversation_id, question, employee_id=None):
        return {"conversation_id": conversation_id, "answer": "Test answer", "sources": []}


def main():
    client = create_app(FakeService()).test_client()
    assert client.get("/health").status_code == 200
    response = client.post("/conversations", json={"user_id": "EMP001"})
    assert response.status_code == 201
    response = client.post("/ask", json={"conversation_id": "test-conversation", "question": "Hello"})
    assert response.status_code == 200
    assert response.get_json()["answer"] == "Test answer"
    assert client.post("/ask", json={}).status_code == 400
    assert client.delete("/conversations/test-conversation").status_code == 200
    print("API test passed: health, conversation, ask, validation, and delete routes")


if __name__ == "__main__":
    main()