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
  mobileHistory: document.querySelector("#mobile-conversation-history"),
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
    elements.mobileHistory.innerHTML = '<span class="history-empty">Add an employee ID to view saved conversations.</span>';
    return;
  }
  try {
    const response = await fetch(`/conversations?user_id=${encodeURIComponent(employeeId)}`);
    const data = await response.json();
    if (requestId !== state.historyRequest) return;
    if (!data.conversations.length) {
      elements.history.innerHTML = '<span class="history-empty">No saved conversations for this ID.</span>';
      elements.mobileHistory.innerHTML = '<span class="history-empty">No saved conversations for this ID.</span>';
      return;
    }
    const historyItems = data.conversations.map((conversation) => {
      const shortId = conversation.conversation_id.slice(0, 8);
      const formattedDate = new Date(conversation.updated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      return `
        <div class="history-item">
          <button class="history-open" type="button" data-conversation-id="${conversation.conversation_id}">
            <span class="history-item-title">${shortId}…</span>
            <small>${formattedDate}</small>
          </button>
          <button class="history-delete" type="button" data-conversation-id="${conversation.conversation_id}" aria-label="Delete conversation ${shortId}" title="Delete conversation">
            <svg class="trash-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
        </div>
      `;
    }).join("");
    elements.history.innerHTML = historyItems;
    elements.mobileHistory.innerHTML = historyItems;
    document.querySelectorAll(".history-open").forEach((item) => item.addEventListener("click", () => reopenConversation(item.dataset.conversationId)));
    document.querySelectorAll(".history-delete").forEach((item) => item.addEventListener("click", () => deleteConversation(item.dataset.conversationId)));
  } catch (error) {
    elements.history.innerHTML = '<span class="history-empty">Conversation history unavailable.</span>';
    elements.mobileHistory.innerHTML = '<span class="history-empty">Conversation history unavailable.</span>';
  }
}

// Initialize global modal event listeners when DOM loads
document.addEventListener("DOMContentLoaded", () => {
  const envDialog = document.querySelector("#test-env-dialog");
  const dismissBtn = document.querySelector("#test-env-dismiss-btn");
  if (envDialog && !sessionStorage.getItem("test_env_notice_dismissed")) {
    envDialog.showModal();
  }
  dismissBtn?.addEventListener("click", () => {
    envDialog?.close();
    sessionStorage.setItem("test_env_notice_dismissed", "true");
  });

  // Attach button '+' modal launcher
  const attachBtn = document.querySelector("#policy-upload-button");
  const uploadDlg = document.querySelector("#upload-dialog");
  const continueBtn = document.querySelector("#upload-dialog-continue");
  const fileInput = document.querySelector("#policy-file");

  attachBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadDlg?.showModal();
  });

  continueBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    uploadDlg?.close();
    fileInput?.click();
  });

  // Policy inspector close buttons — must attach after <dialog> is parsed
  document.querySelector("#reader-close")?.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelector("#policy-reader-dialog")?.close();
  });
  document.querySelector("#reader-done-btn")?.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelector("#policy-reader-dialog")?.close();
  });
});

async function openPolicyReader(filename, title) {
  const dialog = document.querySelector("#policy-reader-dialog");
  const titleEl = document.querySelector("#reader-title");
  const filenameEl = document.querySelector("#reader-filename");
  const contentEl = document.querySelector("#reader-content");
  if (!dialog) return;

  titleEl.textContent = title || "Policy Document";
  filenameEl.textContent = filename;
  contentEl.textContent = "Fetching document content...";
  dialog.showModal();

  try {
    const response = await fetch(`/policies/raw/${encodeURIComponent(filename)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Failed to load document.");
    contentEl.textContent = data.content;
  } catch (error) {
    contentEl.textContent = `Error: ${error.message}`;
  }
}

function attachPolicyRowListeners() {
  document.querySelectorAll(".policy-row").forEach((row) => {
    row.replaceWith(row.cloneNode(true));
  });
  document.querySelectorAll(".policy-row").forEach((row) => {
    row.addEventListener("click", () => {
      const filename = row.dataset.policyFile;
      const title = row.dataset.policyTitle;
      if (filename) openPolicyReader(filename, title);
    });
  });
}

attachPolicyRowListeners();

// Reader close listeners moved into DOMContentLoaded above

async function reopenConversation(conversationId) {
  const response = await fetch(`/conversations/${conversationId}/messages`);
  const data = await response.json();
  state.conversationId = conversationId;
  elements.conversationLabel.textContent = `${conversationId.slice(0, 8)}…`;
  switchView("assistant");
  elements.messages.innerHTML = "";
  data.messages.forEach((message) => addMessage(message.role === "user" ? "user" : "assistant", message.content));
}

async function deleteConversation(conversationId) {
  if (!window.confirm("Delete this conversation and its saved messages?")) return;
  const response = await fetch(`/conversations/${conversationId}`, { method: "DELETE" });
  if (!response.ok) return;
  if (state.conversationId === conversationId) resetConversation();
  loadConversationHistory(historyEmployeeId());
}

function switchView(view) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.viewPanel !== view;
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });
  const introRow = document.querySelector(".intro-row");
  if (introRow) introRow.hidden = view !== "assistant";
  
  const breadcrumbStrong = document.querySelector(".breadcrumb strong");
  if (breadcrumbStrong) {
    breadcrumbStrong.textContent = view === "assistant" ? "Assistant" : view === "policies" ? "Policy Library" : "Employee Profile";
  }
  document.querySelector(".workspace")?.scrollTo({ top: 0, behavior: "smooth" });
}

function setTrace(route, sources) {
  const steps = route === "tool+rag" ? ["Employee eligibility checked", "Policy evidence retrieved", "Trip validated and calculated"] : route === "tool" ? ["Employee record checked", "Tool result prepared"] : ["Policy evidence retrieved", "Grounded answer prepared"];
  elements.trace.innerHTML = steps.map((step, index) => `<div class="trace-item"><span class="trace-number">0${index + 1}</span><span>${step}</span></div>`).join("");
  elements.sourceCount.textContent = `${sources.length} SOURCE${sources.length === 1 ? "" : "S"}`;
  
  if (!sources.length) {
    elements.sources.innerHTML = '<p class="empty-context">No policy documents were needed for this response.</p>';
    return;
  }

  elements.sources.innerHTML = sources.map((source) => `
    <button class="source-item clickable" type="button" data-source-file="${source}" title="Click to view ${source} in Policy Library">
      <span class="source-file-name">${source}</span>
      <span class="source-arrow">↗</span>
    </button>
  `).join("");

  document.querySelectorAll(".source-item.clickable").forEach((btn) => {
    btn.addEventListener("click", () => {
      const filename = btn.dataset.sourceFile;
      if (!filename) return;
      switchView("policies");
      
      const matchingRow = document.querySelector(`.policy-row[data-policy-file="${filename}"]`);
      const title = matchingRow ? matchingRow.dataset.policyTitle : filename;
      openPolicyReader(filename, title);
    });
  });
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
document.querySelectorAll(".prompt-link").forEach((button) => button.addEventListener("click", () => { elements.question.value = button.dataset.prompt; elements.question.focus(); }));

// File upload change handler

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
    
    // Add uploaded policy as a new row in Policy Library list so user can inspect it
    const policyList = document.querySelector(".policy-list");
    if (policyList && !document.querySelector(`.policy-row[data-policy-file="${data.source}"]`)) {
      const newRow = document.createElement("button");
      newRow.className = "policy-row";
      newRow.type = "button";
      newRow.dataset.policyFile = data.source;
      newRow.dataset.policyTitle = data.source;
      newRow.innerHTML = `
        <div class="policy-row-left">
          <span class="policy-icon">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </span>
          <div class="policy-info">
            <strong>${data.source}</strong>
            <small>Custom uploaded policy · ${data.chunks || 1} chunks active in AI assistant</small>
          </div>
        </div>
        <span class="row-arrow">Inspect Document →</span>
      `;
      policyList.appendChild(newRow);
      attachPolicyRowListeners();
    }

    elements.uploadStatus.textContent = `${data.source} is active & indexed in AI search.`;
    elements.uploadStatus.className = "upload-status visible success";
  } catch (error) {
    elements.uploadStatus.textContent = error.message;
    elements.uploadStatus.className = "upload-status visible error";
  } finally {
    elements.policyFile.value = "";
  }
});
document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", (event) => {
  event.preventDefault();
  switchView(item.dataset.view);
  if (item.dataset.view === "profile") setProfile();
}));