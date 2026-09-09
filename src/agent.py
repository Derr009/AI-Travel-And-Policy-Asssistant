"""Decision layer that routes user questions to RAG and business tools."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from rag import PolicyRAG
from tools import (
    calculate_reimbursement,
    check_employee_eligibility,
    validate_trip,
)


EMPLOYEE_PATTERN = re.compile(r"\bEMP\d{3}\b", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"(?:₹|INR\s*)\s*([\d,]+(?:\.\d+)?)|(?:\$|USD\s*)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
TIME_PATTERN = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")


class TravelAssistant:
    """Route questions between policy retrieval, tools, and a local LLM."""

    def __init__(self, rag: PolicyRAG, llm: Any | None = None) -> None:
        self.rag = rag
        self.llm = llm

    @classmethod
    def from_policy_directory(
        cls, policy_dir: str | Path, llm_model: str = "qwen2.5:1.5b"
    ) -> "TravelAssistant":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as error:
            raise RuntimeError("Install langchain-ollama before creating the assistant.") from error
        return cls(
            PolicyRAG.from_policy_directory(policy_dir),
            ChatOllama(model=llm_model, temperature=0),
        )

    def answer(self, question: str) -> Dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("Question must not be empty.")

        employee_id = self._extract_employee_id(question)
        lowered = question.lower()
        if employee_id and self._is_trip_question(lowered):
            return self._answer_trip_question(question, employee_id)
        if employee_id and self._is_eligibility_question(lowered):
            result = check_employee_eligibility(employee_id)
            return {
                "route": "tool",
                "answer": self._generate_answer(
                    question, self._format_eligibility(result), "Employee tool result"
                ),
                "sources": [],
                "tool_results": {"eligibility": result},
            }

        context = self.rag.build_context(question, top_k=3)
        if not context["results"]:
            answer = "I could not find information about that in the available policy documents."
        else:
            answer = self._generate_answer(
                question,
                self._format_policy_answer(context["results"]),
                self._format_retrieved_context(context["results"]),
            )
        return {
            "route": "rag",
            "answer": answer,
            "sources": context["sources"],
            "retrieved": context["results"],
        }

    def _answer_trip_question(self, question: str, employee_id: str) -> Dict[str, Any]:
        employee = check_employee_eligibility(employee_id)
        if employee["status"] == "Not Found":
            return {
                "route": "tool",
                "answer": f"Employee {employee_id} was not found.",
                "sources": [],
                "tool_results": {"eligibility": employee},
            }

        trip_type = "Airport" if "airport" in question.lower() else "Business Travel"
        amount, currency = self._extract_amount(question)
        if amount is None:
            policy_context = self.rag.build_context(
                f"{employee['country']} {trip_type} travel eligibility", top_k=3
            )
            return {
                "route": "tool+rag",
                "answer": self._generate_answer(
                    question,
                    f"{trip_type} trips are permitted when connected to approved business travel.",
                    self._format_retrieved_context(policy_context["results"]),
                ),
                "sources": policy_context["sources"],
                "retrieved": policy_context["results"],
                "tool_results": {"eligibility": employee},
            }
        time_match = TIME_PATTERN.search(question)
        trip_time = time_match.group(0) if time_match else "12:00"
        policy_context = self.rag.build_context(
            f"{employee['country']} {trip_type} travel spending limit", top_k=3
        )
        validation = validate_trip(employee_id, trip_type, amount, trip_time)
        reimbursement = calculate_reimbursement(amount, validation.get("policy_limit", amount))
        evidence = (
            f"Eligibility: {employee}\nValidation: {validation}\n"
            f"Reimbursement: {reimbursement}\n"
            f"Policy context: {self._format_retrieved_context(policy_context['results'])}"
        )
        return {
            "route": "tool+rag",
            "answer": self._generate_answer(
                question, self._format_trip_answer(validation, reimbursement, currency), evidence
            ),
            "sources": policy_context["sources"],
            "retrieved": policy_context["results"],
            "tool_results": {
                "eligibility": employee,
                "validation": validation,
                "reimbursement": reimbursement,
            },
        }

    @staticmethod
    def _extract_employee_id(question: str) -> str | None:
        match = EMPLOYEE_PATTERN.search(question)
        return match.group(0).upper() if match else None

    @staticmethod
    def _extract_amount(question: str) -> tuple[float | None, str]:
        match = AMOUNT_PATTERN.search(question)
        if not match:
            return None, ""
        value = match.group(1) or match.group(2)
        currency = "INR" if match.group(1) else "USD"
        return float(value.replace(",", "")), currency

    @staticmethod
    def _is_eligibility_question(question: str) -> bool:
        return any(word in question for word in ("eligible", "eligibility", "allowed"))

    @staticmethod
    def _is_trip_question(question: str) -> bool:
        return any(word in question for word in ("trip", "ride", "airport", "cost", "costing", "amount"))

    @staticmethod
    def _format_eligibility(result: Dict[str, Any]) -> str:
        if result["status"] == "Not Found":
            return f"Employee {result['employee_id']} was not found."
        return (
            f"{result['employee_id']}: {result['status']}. "
            f"Country: {result['country']}. Employee type: {result['employee_type']}."
        )

    @staticmethod
    def _format_policy_answer(results: list[Dict[str, Any]]) -> str:
        top = results[0]
        return f"Based on {top['metadata']['source']}: {top['text']}"

    @staticmethod
    def _format_retrieved_context(results: list[Dict[str, Any]]) -> str:
        return "\n\n".join(
            f"Source: {item['metadata']['source']}\n{item['text']}" for item in results
        )

    def _generate_answer(self, question: str, fallback: str, evidence: str) -> str:
        if self.llm is None:
            return fallback
        prompt = (
            "You are a corporate travel policy assistant. Answer the user's question "
            "using only the verified evidence below. Do not invent policy rules. "
            "Be concise and mention when approval is required.\n\n"
            f"User question: {question}\n\nVerified evidence:\n{evidence}\n\n"
            "Answer in plain text."
        )
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            return fallback

    @staticmethod
    def _format_trip_answer(
        validation: Dict[str, Any], reimbursement: Dict[str, float], currency: str
    ) -> str:
        if validation["status"] == "Approved":
            return f"The trip is approved. Reimbursable amount: {currency} {reimbursement['reimbursable_amount']:,.2f}."
        reasons = " ".join(validation.get("reasons", [validation.get("reason", "Review required.")]))
        return (
            f"Status: {validation['status']}. {reasons} "
            f"Reimbursable amount: {currency} {reimbursement['reimbursable_amount']:,.2f}."
        )