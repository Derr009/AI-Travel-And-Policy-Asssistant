const state = { conversationId: null, busy: false, historyRequest: 0, historyTimer: null };

const elements = {
  form: document.querySelector("#ask-form"),
  question: document.querySelector("#question"),
  employeeId: document.querySelector("#employee-id"),
  messages: document.querySelector("#messages"),
  welcome: document.querySelector("#welcome-message"),
  send: document.querySelector(".send-button"),
  newChat: document.querySelector("#new-chat-button"),
  sidebarNewChat: document.querySelector("#sidebar-new-chat"),
  clear: document.querySelector("#clear-button"),
  conversationLabel: document.querySelector("#conversation-label"),
  profileId: document.querySelector("#profile-id"),
  profileAvatar: document.querySelector("#profile-avatar"),
  profileStatus: document.querySelector("#profile-status"),
  profileViewAvatar: document.querySelector("#profile-view-avatar"),
  profileViewId: document.querySelector("#profile-view-id"),
  profileViewStatus: document.querySelector("#profile-view-status"),
  profileViewCountry: document.querySelector("#profile-view-country"),
  profileViewType: document.querySelector("#profile-view-type"),
  sources: document.querySelector("#sources-list"),
  sourceCount: document.querySelector("#source-count"),
  trace: document.querySelector("#trace-list"),
  history: document.querySelector("#conversation-history"),
  uploadButton: document.querySelector("#policy-upload-button"),
  policyFile: document.querySelector("#policy-file"),
  uploadStatus: document.querySelector("#upload-status"),
  uploadDialog: document.querySelector("#upload-dialog"),
  uploadDialogClose: document.querySelector("#upload-dialog-close"),
};

function addMessage(role, content, meta = "", jumpToSources = false) {
  document.querySelector(".welcome-message")?.remove();
  const message = document.createElement("div");
  message.className = `message ${role}`;
  const badge = document.createElement("div");
  badge.className = "message-badge";
  badge.textContent = role === "user" ? "" : "A";
  if (role === "assistant") {
    badge.setAttribute("aria-label", "Atlas response");
  }
  const contentBox = document.createElement("div");
  contentBox.className = "message-content";
  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = content;
  contentBox.appendChild(body);
  if (meta) {
    const details = document.createElement("div");
    details.className = `message-meta${jumpToSources ? " source-jump" : ""}`;
    details.textContent = meta;
    if (jumpToSources) {
      details.title = "Show supporting sources";
      details.setAttribute("role", "button");
      details.tabIndex = 0;
      const focusSources = () => {
        document.querySelector(".sources-card")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
        elements.sources.classList.add("evidence-focus");
        window.setTimeout(() => elements.sources.classList.remove("evidence-focus"), 1600);
      };
      details.addEventListener("click", focusSources);
      details.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") focusSources();
      });
    }
    contentBox.appendChild(details);
  }
  message.append(badge, contentBox);
  elements.messages.appendChild(message);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function setProfile() {
  const id = elements.employeeId.value.trim().toUpperCase();
  elements.employeeId.value = id;
  const numericId = id.match(/^EMP(\d{3})$/)?.[1];
  elements.profileAvatar.textContent = numericId || "N";
  elements.profileId.textContent = id || "No employee selected";
  elements.profileStatus.textContent = id ? "Ready for eligibility checks" : "Add an ID to personalize checks";
  elements.profileViewAvatar.textContent = numericId || "N";
  elements.profileViewId.textContent = id || "No employee selected";
  elements.profileViewStatus.textContent = id ? "Profile context ready for validation" : "Enter an ID in the Assistant to load a profile.";
  window.clearTimeout(state.historyTimer);
  state.historyTimer = window.setTimeout(() => loadConversationHistory(id), 250);
  showWelcomeIfConversationEmpty();
}

function historyEmployeeId() {
  const fieldId = elements.employeeId.value.trim().toUpperCase();
  const questionId = elements.question.value.match(/\bEMP\d{3}\b/i)?.[0]?.toUpperCase();
  return fieldId || questionId || "";
}

function scheduleHistoryLookup() {
  window.clearTimeout(state.historyTimer);
  const employeeId = historyEmployeeId();
  state.historyTimer = window.setTimeout(() => loadConversationHistory(employeeId), 250);
}

function showWelcomeIfConversationEmpty() {
  if (elements.messages.querySelector(".message, .loading-dots, .welcome-message")) return;
  elements.messages.appendChild(Object.assign(document.createElement("div"), {
    className: "welcome-message",
    innerHTML: "<div class='welcome-orbit'><img class='idle-search-icon' src='https://img.icons8.com/pulsar-line/48/view-file.png' alt='View policy documents'></div><h2>Policy Query &amp; Validation Console</h2><p>I’ll find the governing policy, check the details, and show you what supports the answer.</p>",
  }));
}

async function loadConversationHistory(employeeId) {
  const requestId = ++state.historyRequest;
  if (!employeeId) {
    elements.history.innerHTML = '<span class="history-empty">Add an employee ID to view saved conversations.</span>';
    return;
  }
  try {
    const response = await fetch(`/conversations?user_id=${encodeURIComponent(employeeId)}`);
    const data = await response.json();
    if (requestId !== state.historyRequest) return;
    if (!data.conversations.length) {
      elements.history.innerHTML = '<span class="history-empty">No saved conversations for this ID.</span>';
      return;
    }
    elements.history.innerHTML = data.conversations.map((conversation) => `<button class="history-item" type="button" data-conversation-id="${conversation.conversation_id}">${conversation.conversation_id.slice(0, 8)}…<small>${new Date(conversation.updated_at).toLocaleDateString()}</small></button>`).join("");
    elements.history.querySelectorAll(".history-item").forEach((item) => item.addEventListener("click", () => reopenConversation(item.dataset.conversationId)));
  } catch (error) {
    elements.history.innerHTML = '<span class="history-empty">Conversation history unavailable.</span>';
  }
}

async function reopenConversation(conversationId) {
  const response = await fetch(`/conversations/${conversationId}/messages`);
  const data = await response.json();
  state.conversationId = conversationId;
  elements.conversationLabel.textContent = `${conversationId.slice(0, 8)}…`;
  switchView("assistant");
  elements.messages.innerHTML = "";
  data.messages.forEach((message) => addMessage(message.role === "user" ? "user" : "assistant", message.content));
}

function switchView(view) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.viewPanel !== view;
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });
  document.querySelector(".intro-row").hidden = view !== "assistant";
  document.querySelector(".workspace")?.scrollTo({ top: 0, behavior: "smooth" });
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
  loading.textContent = "Checking policy details...";
  elements.messages.appendChild(loading);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  try {
    if (!state.conversationId) await createConversation();
    const response = await fetch("/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ conversation_id: state.conversationId, employee_id: elements.employeeId.value.trim() || null, question }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The assistant could not process the request.");
    loading.remove();
    const routeLabel = data.route === "tool+rag" ? "Trip validation" : data.route === "tool" ? "Employee check" : "Policy check";
    addMessage("assistant", data.answer, `${routeLabel}${data.sources?.length ? ` · ${data.sources.length} sources  ↗` : ""}`, Boolean(data.sources?.length));
    setTrace(data.route, data.sources || []);
    const employee = data.tool_results?.eligibility;
    if (employee) {
      elements.profileViewCountry.textContent = employee.country || "Not available";
      elements.profileViewType.textContent = employee.employee_type || "Not available";
      elements.profileViewStatus.textContent = employee.status || "Profile context ready for validation";
    }
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
elements.question.addEventListener("input", () => {
  showWelcomeIfConversationEmpty();
  scheduleHistoryLookup();
});
elements.employeeId.addEventListener("input", setProfile);
function resetConversation() {
  switchView("assistant");
  state.conversationId = null;
  elements.conversationLabel.textContent = "New conversation";
  elements.messages.innerHTML = "";
  elements.messages.appendChild(Object.assign(document.createElement("div"), {
    className: "welcome-message",
    innerHTML: "<div class='welcome-orbit'><img class='idle-search-icon' src='https://img.icons8.com/pulsar-line/48/view-file.png' alt='View policy documents'></div><h2>Policy Query &amp; Validation Console</h2><p>I’ll find the governing policy, check the details, and show you what supports the answer.</p>",
  }));
  elements.sources.innerHTML = '<p class="empty-context">Retrieved policy sources will appear here after your first question.</p>';
  elements.sourceCount.textContent = "0 SOURCES";
}

elements.sidebarNewChat.addEventListener("click", resetConversation);
document.querySelector("#exit-button").addEventListener("click", () => {
  elements.employeeId.value = "";
  setProfile();
  resetConversation();
});
elements.clear.addEventListener("click", async () => { if (!state.conversationId) return; await fetch(`/conversations/${state.conversationId}/clear`, { method: "POST" }); elements.messages.innerHTML = ""; elements.conversationLabel.textContent = "Cleared conversation"; showWelcomeIfConversationEmpty(); });
document.querySelectorAll(".prompt-link").forEach((button) => button.addEventListener("click", () => { elements.question.value = button.dataset.prompt; elements.question.focus(); }));

elements.uploadButton?.addEventListener("click", () => elements.policyFile?.click());
elements.policyFile?.addEventListener("change", async () => {
  const file = elements.policyFile.files[0];
  if (!file) return;
  elements.uploadStatus.textContent = `Uploading ${file.name}...`;
  elements.uploadStatus.className = "upload-status visible";
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch("/policies/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Upload failed.");
    elements.uploadStatus.textContent = `${data.source} is awaiting review.`;
    elements.uploadStatus.className = "upload-status visible success";
    elements.uploadDialog?.showModal();
  } catch (error) {
    elements.uploadStatus.textContent = error.message;
    elements.uploadStatus.className = "upload-status visible error";
  } finally {
    elements.policyFile.value = "";
  }
});
elements.uploadDialogClose?.addEventListener("click", () => elements.uploadDialog?.close());
document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", (event) => {
  event.preventDefault();
  switchView(item.dataset.view);
  if (item.dataset.view === "profile") setProfile();
}));