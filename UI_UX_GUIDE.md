# Uber Atlas UI/UX Guide

A short guide to the visible product experience.

## 1. Header

**Shows:** Workspace, current view, and `Exit assistant`.

**User can:** Exit the active assistant context.

**Result:** The current employee context and conversation view are reset locally. Stored history is not deleted.

## 2. Left Sidebar

### New Conversation

**Purpose:** Start a fresh chat.

**User can:** Click the button at any time.

**Result:** The visible thread resets and a new conversation is created when the next question is submitted.

### Assistant

**Purpose:** Open the main question-and-answer workspace.

**User can:** Ask policy, eligibility, reimbursement, or trip questions.

**Result:** The assistant returns an answer, decision route, and supporting sources when available.

### Policy Library

**Purpose:** Browse the available policy categories.

**User can:** View the read-only policy index.

**Result:** The user sees policy document categories. Detailed retrieval still happens through the Assistant.

### Employee Profile

**Purpose:** View the employee context used for validation.

**User can:** Enter an Employee ID such as `EMP001` in the Assistant.

**Result:** The profile can display the ID, numeric avatar (`001`), country, employee type, and eligibility status.

### Previous Conversations

**Purpose:** Reopen saved conversations for an Employee ID.

**User can:** Enter `EMP001` or mention `EMP001` in a question.

**Result:** Recent saved conversation IDs appear in the sidebar. Selecting one reopens its stored messages.

This is open for the training environment. Production requires authentication and conversation ownership checks.

### Quick Prompts

**Purpose:** Provide common starting questions.

**User can:** Select a prompt such as `India Limits & Thresholds`.

**Result:** The question is placed in the composer for review before sending.

## 3. Main Assistant Workspace

### Hero Area

**Shows:** `Verify Trip Compliance & Policy Limits`.

**Purpose:** Explain the assistant’s primary task without requiring navigation.

### Welcome Console

**Shows:** `Policy Query & Validation Console` when no messages exist.

**Purpose:** Explain that the user can ask a policy or trip question.

**Behavior:** It remains visible while the user types. It disappears after the first submitted question and returns after clearing or starting a new conversation.

## 4. Composer

### Employee ID

**Purpose:** Personalize employee checks.

**User can:** Enter `EMP001`, `emp001`, or leave it blank.

**Result:** IDs are normalized to uppercase. Managers can leave the field blank and ask about an employee directly in the question.

### Question Field

**Purpose:** Enter a natural-language request.

**Examples:**

```text
What is the India travel limit?
Can EMP001 take an airport trip?
What if it costs INR 2,500?
```

**User can:** Press Enter to submit or Shift+Enter for a new line.

### Upload Button

**Purpose:** Submit a fictional `.txt` policy document for review.

**Result:** The document is stored as pending and does not affect answers yet.

The user sees:

```text
Document uploaded and awaiting review. It will not affect answers yet.
```

## 5. Conversation Messages

### User Message

**Shows:** A right-aligned message bubble.

**Purpose:** Display the submitted question.

### Atlas Response

**Shows:** A left-aligned response bubble with an Atlas conversation marker.

**Purpose:** Display the generated answer.

**Can include:**

- Policy explanation
- Eligibility result
- Trip approval status
- Reimbursable amount
- Amount requiring review
- Follow-up interpretation

## 6. Response Metadata

Under an answer, the user may see labels such as:

```text
Policy check · 2 sources
Employee check
Trip validation · 2 sources
```

**User can:** Click the source link when sources are available.

**Result:** The Evidence section scrolls into view and highlights the supporting sources.

## 7. Right Context Rail

### Employee Profile

**Shows:** Employee ID, numeric avatar, country, employee type, and status when available.

**Purpose:** Make the employee context visible while reviewing a request.

### Decision Trace

**Shows:** High-level processing steps such as:

```text
Employee record checked
Policy evidence retrieved
Trip validated and calculated
```

**Purpose:** Make the assistant’s decision path understandable without exposing technical internals.

### Evidence

**Shows:** Policy source filenames and retrieved references.

**Purpose:** Support answer transparency and reduce unsupported claims.

### Grounding Note

**Shows:** A reminder that answers are based on the fictional policy library and employee records.

**Purpose:** Set expectations around the training environment.

## 8. Clear Thread vs Exit Assistant

### Clear Thread

**Result:** Removes visible messages and deletes stored messages/state for the current conversation. The conversation record remains.

### Exit Assistant

**Result:** Clears the local employee context and resets the visible assistant view. Stored conversation history remains available.

## 9. Typical User Flow

```text
Enter Employee ID or ask about an employee
        ↓
Review previous conversations if available
        ↓
Ask a policy or trip question
        ↓
Read the response and decision route
        ↓
Open supporting Evidence
        ↓
Continue the conversation or start a new one
```
