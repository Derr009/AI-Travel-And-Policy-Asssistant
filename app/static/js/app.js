const state = { conversationId: null, busy: false };

const elements = {
  form: document.querySelector("#ask-form"),
  question: document.querySelector("#question"),
  employeeId: document.querySelector("#employee-id"),
  messages: document.querySelector("#messages"),
  welcome: document.querySelector("#welcome-message"),
  send: document.querySelector(".send-button"),
  newChat: document.querySelector("#new-chat-button"),
  clear: document.querySelector("#clear-button"),
  conversationLabel: document.querySelector("#conversation-label"),
  profileId: document.querySelector("#profile-id"),
  profileStatus: document.querySelector("#profile-status"),
  sources: document.querySelector("#sources-list"),
  sourceCount: document.querySelector("#source-count"),
  trace: document.querySelector("#trace-list"),
};

function addMessage(role, content, meta = "") {
  elements.welcome?.remove();
  const message = document.createElement("div");
  message.className = `message ${role}`;
  const badge = document.createElement("div");
  badge.className = "message-badge";
  badge.textContent = role === "user" ? "YOU" : "AI";
  const contentBox = document.createElement("div");
  contentBox.className = "message-content";
  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = content;
  contentBox.appendChild(body);
  if (meta) {
    const details = document.createElement("div");
    details.className = "message-meta";
    details.textContent = meta;
    contentBox.appendChild(details);
  }
  message.append(badge, contentBox);
  elements.messages.appendChild(message);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function setProfile() {
  const id = elements.employeeId.value.trim().toUpperCase();
  elements.profileId.textContent = id || "No employee selected";
  elements.profileStatus.textContent = id ? "Ready for eligibility checks" : "Add an ID to personalize checks";
}

function setTrace(route, sources) {
  const steps = route === "tool+rag" ? ["Employee eligibility checked", "Policy evidence retrieved", "Trip validated and calculated"] : route === "tool" ? ["Employee record checked", "Tool result prepared"] : ["Policy evidence retrieved", "Grounded answer prepared"];
  elements.trace.innerHTML = steps.map((step, index) => `<div class="trace-item"><span class="trace-number">0${index + 1}</span><span>${step}</span></div>`).join("");
  elements.sourceCount.textContent = `${sources.length} SOURCE${sources.length === 1 ? "" : "S"}`;
  elements.sources.innerHTML = sources.length ? sources.map((source) => `<div class="source-item">${source}</div>`).join("") : '<p class="empty-context">No policy documents were needed for this response.</p>';
}

async function createConversation() {
  const response = await fetch("/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: elements.employeeId.value.trim() || null }) });
  if (!response.ok) throw new Error("Could not create a conversation.");
  const data = await response.json();
  state.conversationId = data.conversation_id;
  elements.conversationLabel.textContent = `${state.conversationId.slice(0, 8)}…`;
}

async function ask(question) {
  if (state.busy) return;
  state.busy = true;
  elements.send.disabled = true;
  addMessage("user", question);
  const loading = document.createElement("div");
  loading.className = "message assistant loading-dots";
  loading.textContent = "AI is checking policy evidence...";
  elements.messages.appendChild(loading);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  try {
    if (!state.conversationId) await createConversation();
    const response = await fetch("/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ conversation_id: state.conversationId, employee_id: elements.employeeId.value.trim() || null, question }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The assistant could not process the request.");
    loading.remove();
    addMessage("assistant", data.answer, `${data.route.toUpperCase()}${data.sources?.length ? ` · ${data.sources.length} sources` : ""}`);
    setTrace(data.route, data.sources || []);
  } catch (error) {
    loading.remove();
    addMessage("assistant", error.message, "ERROR");
  } finally {
    state.busy = false;
    elements.send.disabled = false;
    elements.question.focus();
  }
}

elements.form.addEventListener("submit", (event) => { event.preventDefault(); const question = elements.question.value.trim(); if (!question) return; elements.question.value = ""; ask(question); });
elements.question.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); elements.form.requestSubmit(); } });
elements.employeeId.addEventListener("input", setProfile);
elements.newChat.addEventListener("click", () => { state.conversationId = null; elements.conversationLabel.textContent = "New conversation"; elements.messages.innerHTML = ""; elements.messages.appendChild(elements.welcome || Object.assign(document.createElement("div"), { className: "welcome-message", innerHTML: "<div class='welcome-orbit'><span>✦</span></div><h2>Bring me the question.</h2><p>I’ll find the governing policy, check the details, and show you what supports the answer.</p>" })); elements.sources.innerHTML = '<p class="empty-context">Retrieved policy sources will appear here after your first question.</p>'; elements.sourceCount.textContent = "0 SOURCES"; });
elements.clear.addEventListener("click", async () => { if (!state.conversationId) return; await fetch(`/conversations/${state.conversationId}/clear`, { method: "POST" }); elements.messages.innerHTML = ""; elements.conversationLabel.textContent = "Cleared conversation"; });
document.querySelectorAll(".prompt-link").forEach((button) => button.addEventListener("click", () => { elements.question.value = button.dataset.prompt; elements.question.focus(); }));