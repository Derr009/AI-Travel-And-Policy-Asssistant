# REST API Documentation

This project exposes a lightweight Flask API for the AI Travel and Policy Assistant.

## Base URL

- Local dev: `http://127.0.0.1:5000`

## Endpoints

### GET /health
Returns service health.

Response example:

```json
{
  "status": "ok",
  "service": "travel-policy-assistant"
}
```

### POST /conversations
Creates a new conversation.

Request body:

```json
{
  "user_id": "EMP001"
}
```

Response:

```json
{
  "conversation_id": "<conversation-id>",
  "status": "active"
}
```

### GET /conversations
Lists conversations for a user.

Query params:

- `user_id` (optional): employee ID filter

Example:

```http
GET /conversations?user_id=EMP001
```

Response:

```json
{
  "conversations": [
    {
      "conversation_id": "abc123",
      "user_id": "EMP001",
      "created_at": "2026-09-14T12:00:00"
    }
  ]
}
```

### GET /conversations/<conversation_id>/messages
Gets recent message history for a conversation.

Response:

```json
{
  "conversation_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "Can EMP001 travel tonight?"
    }
  ]
}
```

### POST /ask
Sends a user question to the assistant.

Request body:

```json
{
  "conversation_id": "abc123",
  "employee_id": "EMP001",
  "question": "Can EMP001 take an airport trip costing ₹2,500 tonight?"
}
```

Response:

```json
{
  "conversation_id": "abc123",
  "answer": "Employee EMP001 is eligible...",
  "sources": ["travel_policy_india.txt"],
  "status": "ok"
}
```

### DELETE /conversations/<conversation_id>
Deletes a conversation and its stored messages.

Response:

```json
{
  "conversation_id": "abc123",
  "status": "deleted"
}
```

### GET /policies/raw/<filename>
Returns raw text for a policy file.

Example:

```http
GET /policies/raw/travel_policy_india.txt
```

### POST /policies/upload
Uploads a new policy file into the active policy directory and reloads the vector index.

Form data:

- `file`: text file upload

Response:

```json
{
  "status": "active",
  "source": "travel_policy_uk.txt",
  "chunks": 24
}
```

## Notes

- `employee_id` is optional in the UI, but useful for personalized policy checks and history.
- Answers combine policy retrieval, employee validation, and deterministic trip logic.
- Errors return JSON with an `error` field and an HTTP status code.
