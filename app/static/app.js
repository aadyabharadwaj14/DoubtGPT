const SESSION_STORAGE_KEY = "doubtgpt-session-id";
let sessionId = getOrCreateSessionId();

const elements = {
  form: document.getElementById("chat-form"),
  input: document.getElementById("chat-input"),
  messageList: document.getElementById("message-list"),
  status: document.getElementById("request-status"),
  sendButton: document.getElementById("send-button"),
  debugCheckbox: document.getElementById("debug-checkbox"),
  template: document.getElementById("message-template"),
  healthPill: document.getElementById("health-pill"),
  providerValue: document.getElementById("provider-value"),
  sampleValue: document.getElementById("sample-value"),
  agreementValue: document.getElementById("agreement-value"),
  fastPathValue: document.getElementById("fast-path-value"),
  sessionList: document.getElementById("session-list"),
  newChatButton: document.getElementById("new-chat-button"),
  sessionLabel: document.getElementById("session-label"),
  renameChatButton: document.getElementById("rename-chat-button"),
  deleteChatButton: document.getElementById("delete-chat-button"),
};

function setRequestState(text, busy = false) {
  elements.status.textContent = text;
  elements.sendButton.disabled = busy;
}

function appendUserMessage(text) {
  const node = elements.template.content.firstElementChild.cloneNode(true);
  node.classList.add("message-user");
  node.querySelector(".speaker").textContent = "You";
  node.querySelector(".message-text").textContent = text;
  elements.messageList.appendChild(node);
  scrollToBottom();
}

function appendAssistantMessage(payload) {
  const node = elements.template.content.firstElementChild.cloneNode(true);
  node.classList.add("message-assistant");
  node.querySelector(".speaker").textContent = "DoubtGPT";
  node.querySelector(".message-text").textContent = payload.response || payload.content;

  const badgeRow = node.querySelector(".badge-row");
  if (payload.decision) {
    badgeRow.appendChild(buildBadge(payload.decision, payload.decision));
  }
  if (typeof payload.confidence === "number") {
    badgeRow.appendChild(
      buildBadge("confidence", `${Math.round(payload.confidence * 100)}% confidence`)
    );
  }

  if (payload.reason) {
    const reason = document.createElement("p");
    reason.className = "message-text";
    reason.textContent = `Why: ${payload.reason}`;
    node.appendChild(reason);
  }

  const debugDetails = node.querySelector(".debug-details");
  if (payload.debug) {
    debugDetails.hidden = false;
    debugDetails.querySelector(".debug-json").textContent = JSON.stringify(
      payload.debug,
      null,
      2
    );
  }

  elements.messageList.appendChild(node);
  scrollToBottom();
}

function clearRenderedMessages() {
  const messages = elements.messageList.querySelectorAll(".message:not(.intro-card)");
  messages.forEach((message) => message.remove());
}

function renderSessionLabel() {
  elements.sessionLabel.textContent = `Session: ${sessionId}`;
}

function buildBadge(type, text) {
  const badge = document.createElement("span");
  badge.className = `badge ${type}`;
  badge.textContent = text;
  return badge;
}

function scrollToBottom() {
  elements.messageList.scrollTop = elements.messageList.scrollHeight;
}

async function loadHealth() {
  try {
    const response = await fetch("/health");
    const health = await response.json();
    elements.providerValue.textContent = health.provider;
    elements.sampleValue.textContent = health.gemini_sample_count;
    elements.agreementValue.textContent = health.semantic_agreement_enabled === "true"
      ? "semantic"
      : "lexical";
    elements.fastPathValue.textContent = health.fast_path_enabled;
    elements.healthPill.textContent = "Ready";
    elements.healthPill.className = "pill good";
  } catch (error) {
    elements.healthPill.textContent = "Offline";
    elements.healthPill.className = "pill warn";
    elements.status.textContent = "Could not reach the API.";
  }
}

async function loadSessionHistory() {
  try {
    const response = await fetch(`/sessions/${sessionId}/messages`);
    if (!response.ok) {
      throw new Error(`History request failed with status ${response.status}`);
    }

    const messages = await response.json();
    clearRenderedMessages();
    messages.forEach((message) => {
      if (message.role === "user") {
        appendUserMessage(message.content);
      } else {
        appendAssistantMessage(message);
      }
    });
    if (messages.length > 0) {
      setRequestState(`Loaded ${messages.length} saved messages`);
    } else {
      setRequestState("Ready");
    }
  } catch (error) {
    setRequestState("Could not load previous messages");
  }
}

async function loadSessionList() {
  try {
    const response = await fetch("/sessions");
    if (!response.ok) {
      throw new Error(`Session list failed with status ${response.status}`);
    }

    const sessions = await response.json();
    elements.sessionList.innerHTML = "";

    if (sessions.length === 0) {
      const empty = document.createElement("div");
      empty.className = "session-meta";
      empty.textContent = "No saved chats yet.";
      elements.sessionList.appendChild(empty);
      return;
    }

    sessions.forEach((session) => {
      const row = document.createElement("div");
      row.className = "session-row";

      const button = document.createElement("button");
      button.type = "button";
      button.className = "session-item";
      if (session.session_id === sessionId) {
        button.classList.add("active");
      }
      button.innerHTML = `
        <span class="session-preview">${escapeHtml(session.preview)}</span>
        <span class="session-meta">${session.message_count} messages</span>
      `;
      button.addEventListener("click", async () => {
        sessionId = session.session_id;
        window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
        renderSessionLabel();
        await loadSessionHistory();
        await loadSessionList();
      });

      const renameButton = document.createElement("button");
      renameButton.type = "button";
      renameButton.className = "mini-button icon";
      renameButton.textContent = "Edit";
      renameButton.addEventListener("click", async () => {
        await promptRenameSession(session.session_id, session.title || session.preview);
      });

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "mini-button icon danger";
      deleteButton.textContent = "Del";
      deleteButton.addEventListener("click", async () => {
        await removeSession(session.session_id);
      });

      row.appendChild(button);
      row.appendChild(renameButton);
      row.appendChild(deleteButton);
      elements.sessionList.appendChild(row);
    });
  } catch (error) {
    elements.sessionList.innerHTML = '<div class="session-meta">Could not load chats.</div>';
  }
}

async function sendMessage(message) {
  appendUserMessage(message);
  setRequestState("DoubtGPT is thinking...", true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        include_debug: elements.debugCheckbox.checked,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const payload = await response.json();
    appendAssistantMessage(payload);
    const latency = payload.debug?.latency_ms;
    setRequestState(
      latency ? `Last reply took ${latency} ms` : "Reply received",
      false
    );
    await loadSessionList();
  } catch (error) {
    appendAssistantMessage({
      decision: "abstain",
      confidence: 0,
      response: "The UI could not reach the backend. Check whether the FastAPI server is running.",
      reason: String(error),
    });
    setRequestState("Request failed", false);
  }
}

async function promptRenameSession(targetSessionId = sessionId, currentTitle = "") {
  const nextTitle = window.prompt("Rename chat", currentTitle || "");
  if (!nextTitle || !nextTitle.trim()) {
    return;
  }

  const response = await fetch(`/sessions/${targetSessionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: nextTitle.trim() }),
  });

  if (!response.ok) {
    setRequestState("Could not rename chat");
    return;
  }

  if (targetSessionId === sessionId) {
    setRequestState(`Renamed chat to "${nextTitle.trim()}"`);
  }
  await loadSessionList();
}

async function removeSession(targetSessionId) {
  const confirmed = window.confirm("Delete this chat permanently?");
  if (!confirmed) {
    return;
  }

  const response = await fetch(`/sessions/${targetSessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    setRequestState("Could not delete chat");
    return;
  }

  if (targetSessionId === sessionId) {
    startNewChat();
  } else {
    await loadSessionList();
  }
}

function getOrCreateSessionId() {
  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const created = `web-${Math.random().toString(36).slice(2, 10)}`;
  window.localStorage.setItem(SESSION_STORAGE_KEY, created);
  return created;
}

function startNewChat() {
  sessionId = `web-${Math.random().toString(36).slice(2, 10)}`;
  window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  renderSessionLabel();
  clearRenderedMessages();
  setRequestState("Started a new chat");
  loadSessionList();
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = elements.input.value.trim();
  if (!message) {
    return;
  }

  elements.input.value = "";
  await sendMessage(message);
});

document.querySelectorAll(".prompt-chip").forEach((button) => {
  button.addEventListener("click", async () => {
    const prompt = button.dataset.prompt;
    if (!prompt) {
      return;
    }

    elements.input.value = "";
    await sendMessage(prompt);
  });
});

elements.newChatButton.addEventListener("click", startNewChat);
elements.renameChatButton.addEventListener("click", async () => {
  await promptRenameSession();
});
elements.deleteChatButton.addEventListener("click", async () => {
  await removeSession(sessionId);
});

renderSessionLabel();
loadHealth();
loadSessionHistory();
loadSessionList();
