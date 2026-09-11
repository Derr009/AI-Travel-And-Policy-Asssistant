"""Flask JSON API for the travel and policy assistant."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from conversation_service import ConversationService


def create_app(service: Any | None = None) -> Flask:
    app = Flask(__name__)
    conversation_service = service or ConversationService.from_policy_directory(
        PROJECT_ROOT / "data" / "company_policy"
    )
    policy_directory = PROJECT_ROOT / "data" / "company_policy"
    pending_policy_directory = PROJECT_ROOT / "data" / "company_policy_pending"

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "travel-policy-assistant"})

    @app.post("/policies/upload")
    def upload_policy():
        uploaded_file = request.files.get("file")
        if uploaded_file is None or not uploaded_file.filename:
            return jsonify({"error": "A policy text file is required."}), 400
        filename = secure_filename(uploaded_file.filename)
        if not filename.lower().endswith(".txt"):
            return jsonify({"error": "Only .txt policy files are supported."}), 400
        content = uploaded_file.read()
        if not content.strip():
            return jsonify({"error": "The policy file cannot be empty."}), 400
        if len(content) > 1_000_000:
            return jsonify({"error": "Policy files must be smaller than 1 MB."}), 400
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "Policy files must use UTF-8 text."}), 400

        pending_policy_directory.mkdir(parents=True, exist_ok=True)
        uploaded_file.stream.seek(0)
        uploaded_file.save(pending_policy_directory / filename)
        return jsonify({"status": "pending_review", "source": filename}), 201

    @app.post("/conversations")
    def create_conversation():
        payload = request.get_json(silent=True) or {}
        conversation_id = conversation_service.create_conversation(payload.get("user_id"))
        return jsonify({"conversation_id": conversation_id, "status": "active"}), 201

    @app.get("/conversations")
    def list_conversations():
        user_id = request.args.get("user_id", "")
        return jsonify({"conversations": conversation_service.memory.list_conversations(user_id)})

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

    @app.delete("/conversations/<conversation_id>")
    def delete_conversation(conversation_id: str):
        conversation_service.memory.delete_conversation(conversation_id)
        return jsonify({"conversation_id": conversation_id, "status": "deleted"})

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "The requested resource was not found."}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled API error", exc_info=error)
        return jsonify({"error": "The assistant could not process the request."}), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True, host="127.0.0.1", port=5000)


app = create_app()