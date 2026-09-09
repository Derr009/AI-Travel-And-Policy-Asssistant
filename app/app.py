"""Flask JSON API for the travel and policy assistant."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from conversation_service import ConversationService


def create_app(service: Any | None = None) -> Flask:
    app = Flask(__name__)
    conversation_service = service or ConversationService.from_policy_directory(
        PROJECT_ROOT / "data" / "company_policy"
    )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "travel-policy-assistant"})

    @app.post("/conversations")
    def create_conversation():
        payload = request.get_json(silent=True) or {}
        conversation_id = conversation_service.create_conversation(payload.get("user_id"))
        return jsonify({"conversation_id": conversation_id, "status": "active"}), 201

    @app.post("/ask")
    def ask():
        payload = request.get_json(silent=True) or {}
        conversation_id = payload.get("conversation_id")
        question = payload.get("question")
        if not conversation_id or not question:
            return jsonify({"error": "conversation_id and question are required."}), 400
        result = conversation_service.ask(
            conversation_id,
            question,
            employee_id=payload.get("employee_id"),
        )
        return jsonify(result)

    @app.get("/conversations/<conversation_id>/messages")
    def get_messages(conversation_id: str):
        messages = conversation_service.memory.get_recent_messages(conversation_id)
        return jsonify({"conversation_id": conversation_id, "messages": messages})

    @app.post("/conversations/<conversation_id>/clear")
    def clear_conversation(conversation_id: str):
        conversation_service.memory.clear_conversation(conversation_id)
        return jsonify({"conversation_id": conversation_id, "status": "cleared"})

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled API error", exc_info=error)
        return jsonify({"error": "The assistant could not process the request."}), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True, host="127.0.0.1", port=5000)