"""Application service joining persistent memory with the travel and policy agent."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from agent import TravelAssistant
from memory import ConversationMemory


EMPLOYEE_PATTERN = re.compile(r"\bEMP\d{3}\b", re.IGNORECASE)


class ConversationService:
    """Manage a conversation across requests without sending full history to the LLM."""

    def __init__(self, assistant: TravelAssistant, memory: ConversationMemory) -> None:
        self.assistant = assistant
        self.memory = memory

    @classmethod
    def from_policy_directory(cls, policy_dir: str | Path) -> "ConversationService":
        return cls(
            TravelAssistant.from_policy_directory(policy_dir),
            ConversationMemory(),
        )

    def create_conversation(self, user_id: str | None = None) -> str:
        return self.memory.create_conversation(user_id=user_id)

    def ask(
        self,
        conversation_id: str,
        question: str,
        employee_id: str | None = None,
    ) -> Dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("Question must not be empty.")

        state = self.memory.get_state(conversation_id)
        resolved_question = self._resolve_question(question, state, employee_id)
        self.memory.add_message(conversation_id, "user", question)
        result = self.assistant.answer(resolved_question)
        self.memory.add_message(conversation_id, "assistant", result["answer"])
        self.memory.update_state(conversation_id, self._next_state(state, result, resolved_question))
        return {
            "conversation_id": conversation_id,
            "question": question,
            **result,
            "messages": self.memory.get_recent_messages(conversation_id),
            "state": self.memory.get_state(conversation_id),
        }

    @staticmethod
    def _resolve_question(
        question: str, state: Dict[str, Any], employee_id: str | None
    ) -> str:
        resolved_employee_id = employee_id or state.get("employee_id")
        additions = []
        if resolved_employee_id and not EMPLOYEE_PATTERN.search(question):
            additions.append(f"Employee ID: {resolved_employee_id}")
        if state.get("trip_type") and any(
            word in question.lower() for word in ("it", "this", "that")
        ):
            additions.append(f"The referenced trip type is {state['trip_type']}.")
        return f"{question.strip()} ({' '.join(additions)})" if additions else question.strip()

    @staticmethod
    def _next_state(
        previous_state: Dict[str, Any], result: Dict[str, Any], resolved_question: str
    ) -> Dict[str, Any]:
        state = dict(previous_state)
        tool_results = result.get("tool_results", {})
        eligibility = tool_results.get("eligibility", {})
        validation = tool_results.get("validation", {})
        employee_match = EMPLOYEE_PATTERN.search(resolved_question)
        if employee_match:
            state["employee_id"] = employee_match.group(0).upper()
        if eligibility.get("employee_id"):
            state["employee_id"] = eligibility["employee_id"]
        if eligibility.get("country"):
            state["country"] = eligibility["country"]
        if validation.get("trip_type"):
            state["trip_type"] = validation["trip_type"]
        elif "airport" in resolved_question.lower():
            state["trip_type"] = "Airport"
        if validation.get("amount") is not None:
            state["amount"] = validation["amount"]
        return state