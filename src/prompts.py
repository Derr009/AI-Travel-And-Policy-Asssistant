"""Prompt templates for policy classification and summarization."""


POLICY_CLASSIFICATION_PROMPT = """
You are a corporate travel policy analyst.

Task:
Classify the user question and answer it only when the supplied policy context
contains enough information.

Context:
Use only the policy context below. Do not invent limits, approvals, employees,
or reimbursements. If the answer is not supported, classify it as unsupported.

Few-shot examples:
Question: What is the standard travel limit in India?
Output: {{"category": "policy_question", "supported": true}}

Question: Is EMP001 eligible for business travel?
Output: {{"category": "eligibility_check", "supported": true}}

Question: Does the company reimburse hotel bookings?
Output: {{"category": "unsupported", "supported": false}}

User question:
{question}

Policy context:
{context}

Return valid JSON only, using this structure:
{{
	"category": "policy_question|eligibility_check|trip_validation|reimbursement|unsupported",
	"supported": true,
	"answer": " concise answer grounded in the context ",
	"sources": ["source_filename.txt"],
	"confidence": 0.0
}}
""".strip()


POLICY_SUMMARY_PROMPT = """
You are a corporate travel policy analyst.

Task:
Summarize the supplied policy document for employees.

Context:
Preserve all important limits, eligibility rules, approval requirements,
exceptions, time windows, and required information. Do not add information
that is not present in the document.

Format:
Return valid JSON only:
{{
	"source": "source_filename.txt",
	"policy_type": "travel|airport|expense|approval|cancellation|eligibility|general",
	"summary": "short employee-friendly summary",
	"key_rules": ["rule 1", "rule 2"],
	"limits": ["limit or none stated"],
	"approval_requirements": ["requirement or none stated"]
}}

Document source: {source}
Document content:
{document}
""".strip()


def build_classification_prompt(question: str, context: str) -> str:
		"""Build a grounded classification prompt for an LLM."""
		return POLICY_CLASSIFICATION_PROMPT.format(question=question, context=context)


def build_summary_prompt(source: str, document: str) -> str:
		"""Build a structured policy-summary prompt for an LLM."""
		return POLICY_SUMMARY_PROMPT.format(source=source, document=document)
