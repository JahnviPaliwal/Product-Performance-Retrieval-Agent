/* ── BI RAG Assistant – app.js ── */

const chatMessages   = document.getElementById("chatMessages");
const chatInput      = document.getElementById("chatInput");
const sendBtn        = document.getElementById("sendBtn");
const fileInput      = document.getElementById("fileInput");
const dropZone       = document.getElementById("dropZone");
const uploadProgress = document.getElementById("uploadProgress");
const uploadStatus   = document.getElementById("uploadStatus");
const docList        = document.getElementById("docList");
const docCount       = document.getElementById("docCount");
const suggestionsList = document.getElementById("suggestionsList");
const chartsPanel    = document.getElementById("chartsPanel");
const chartsGrid     = document.getElementById("chartsGrid");
const loadingOverlay = document.getElementById("loadingOverlay");
const loadingMsg     = document.getElementById("loadingMsg");
const apiKeyInput    = document.getElementById("apiKeyInput");

// ── Persist API key in sessionStorage ──
apiKeyInput.value = sessionStorage.getItem("groq_api_key") || "";
apiKeyInput.addEventListener("change", () => {
  sessionStorage.setItem("groq_api_key", apiKeyInput.value.trim());
});

// ── Drop Zone ──
dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault(); dropZone.classList.remove("drag-over");
  uploadFiles(e.dataTransfer.files);
});
fileInput.addEventListener("change", () => uploadFiles(fileInput.files));

// ── Enter to send ──
chatInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ── Suggestion chips ──
suggestionsList.addEventListener("click", e => {
  const item = e.target.closest(".suggestion-item");
  if (item) { chatInput.value = item.dataset.q; sendMessage(); }
});

// ── Upload ──────────────────────────────────────────────────────────────────
async function uploadFiles(files) {
  if (!files || files.length === 0) return;
  uploadProgress.classList.remove("hidden");

  for (const file of Array.from(files)) {
    uploadStatus.textContent = `Uploading: ${file.name}…`;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.error) {
        showToast(`❌ ${data.error}`, "error");
      } else {
        showToast(`✅ ${data.filename} uploaded & indexed.`, "success");
        await refreshDocList();
      }
    } catch (err) {
      showToast(`❌ Upload failed: ${err.message}`, "error");
    }
  }

  uploadProgress.classList.add("hidden");
  fileInput.value = "";
}

// ── Document list ────────────────────────────────────────────────────────────
async function refreshDocList() {
  const res  = await fetch("/api/documents");
  const data = await res.json();
  const docs = data.documents || [];

  docCount.textContent = docs.length;

  if (docs.length === 0) {
    docList.innerHTML = '<li class="doc-empty">No documents uploaded yet.</li>';
    return;
  }

  docList.innerHTML = docs.map(doc => `
    <li class="doc-item" data-id="${doc.doc_id}">
      <span class="doc-type-badge badge-${doc.file_type}">${doc.file_type}</span>
      <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
      <button class="btn-delete" onclick="deleteDocument('${doc.doc_id}')" title="Delete">✕</button>
    </li>
  `).join("");
}

async function deleteDocument(docId) {
  if (!confirm("Delete this document and its embeddings?")) return;
  const res  = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
  const data = await res.json();
  if (data.error) {
    showToast(`❌ ${data.error}`, "error");
  } else {
    showToast("🗑️ Document deleted.", "success");
    await refreshDocList();
  }
}

// ── Send Message ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const query  = chatInput.value.trim();
  const apiKey = apiKeyInput.value.trim();

  if (!query) return;
  if (!apiKey) { showToast("⚠️ Please enter your Groq API key.", "error"); return; }

  // Append user message
  appendMessage("user", query);
  chatInput.value = "";

  // Show typing indicator
  const typingId = showTyping();

  setLoading(true, "Agent reasoning…");
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, api_key: apiKey }),
    });
    const data = await res.json();

    removeTyping(typingId);
    setLoading(false);
    sendBtn.disabled = false;

    if (data.error) {
      appendError(data.error);
      return;
    }

    appendAssistantMessage(data);

    // Update suggestion chips from followups
    if (data.followups && data.followups.length > 0) {
      updateSuggestions(data.followups);
    }

    // Show charts if present
    if (data.charts && data.charts.length > 0) {
      renderCharts(data.charts);
    }

  } catch (err) {
    removeTyping(typingId);
    setLoading(false);
    sendBtn.disabled = false;
    appendError(`Network error: ${err.message}`);
  }
}

// ── Message Renderers ────────────────────────────────────────────────────────
function appendMessage(role, text) {
  // Remove welcome message if present
  const welcome = chatMessages.querySelector(".welcome-msg");
  if (welcome) welcome.remove();

  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-bubble"><div class="msg-content">${escapeHtml(text)}</div></div>
    <div class="msg-meta">${role === "user" ? "You" : "Assistant"} · ${timeNow()}</div>
  `;
  chatMessages.appendChild(div);
  scrollBottom();
}

function appendAssistantMessage(data) {
  const welcome = chatMessages.querySelector(".welcome-msg");
  if (welcome) welcome.remove();

  const div = document.createElement("div");
  div.className = "msg assistant";

  const modeLabel = { rag: "📄 Document Mode", analytics: "📊 Analytics Mode", general: "🌐 General Knowledge" };
  const modeClass = { rag: "mode-rag", analytics: "mode-analytics", general: "mode-general" };

  let html = "";

  // Irrelevant notice
  if (data.is_irrelevant) {
    html += `<div class="notice-banner">
      <strong>⚠️ Notice:</strong> The information you are asking for is not present in the uploaded document(s).
      The answer below is generated using general knowledge and external LLM reasoning, not your uploaded files.
    </div>`;
  }

  html += `<div class="msg-bubble">`;

  // Mode badge
  html += `<span class="mode-badge ${modeClass[data.mode] || "mode-general"}">${modeLabel[data.mode] || "General"}</span>`;

  // Answer
  html += `<div class="msg-content">${formatAnswer(data.answer)}</div>`;

  // Sources
  if (data.sources && data.sources.length > 0) {
    html += `<div class="sources-wrap">📎 Sources: <span>${data.sources.join(", ")}</span></div>`;
  }

  // Follow-ups
  if (data.followups && data.followups.length > 0) {
    const chips = data.followups.map(q =>
      `<span class="followup-chip" onclick="setQuery(this)">${escapeHtml(q)}</span>`
    ).join("");
    html += `<div class="followups-wrap">
      <div class="followups-title">💡 Follow-up questions:</div>
      <div class="followup-chips">${chips}</div>
    </div>`;
  }

  html += `</div>`;
  html += `<div class="msg-meta">Assistant · ${timeNow()}</div>`;

  div.innerHTML = html;
  chatMessages.appendChild(div);
  scrollBottom();
}

function appendError(msg) {
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = `<div class="msg-bubble" style="background:#FFEBEE;border-color:#EF9A9A;color:#C62828;">
    ❌ ${escapeHtml(msg)}
  </div>`;
  chatMessages.appendChild(div);
  scrollBottom();
}

// ── Typing Indicator ─────────────────────────────────────────────────────────
function showTyping() {
  const id = "typing-" + Date.now();
  const div = document.createElement("div");
  div.className = "msg assistant"; div.id = id;
  div.innerHTML = `<div class="msg-bubble"><div class="typing-indicator">
    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
  </div></div>`;
  chatMessages.appendChild(div);
  scrollBottom();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Charts ───────────────────────────────────────────────────────────────────
function renderCharts(charts) {
  chartsGrid.innerHTML = "";
  charts.forEach(c => {
    const card = document.createElement("div");
    card.className = "chart-card";
    card.innerHTML = `
      <div class="chart-title">${escapeHtml(c.title)}</div>
      <img class="chart-img" src="data:image/png;base64,${c.image_b64}" alt="${escapeHtml(c.title)}"/>
    `;
    chartsGrid.appendChild(card);
  });
  chartsPanel.classList.remove("hidden");
}

// ── Suggestions ──────────────────────────────────────────────────────────────
function updateSuggestions(questions) {
  suggestionsList.innerHTML = questions.map(q =>
    `<li class="suggestion-item" data-q="${escapeAttr(q)}">${escapeHtml(q)}</li>`
  ).join("");
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function setQuery(el) {
  chatInput.value = el.textContent;
  chatInput.focus();
}

function setLoading(show, msg = "Thinking…") {
  loadingMsg.textContent = msg;
  loadingOverlay.classList.toggle("hidden", !show);
}

function scrollBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function escapeAttr(str) {
  return String(str).replace(/"/g, "&quot;");
}

function formatAnswer(text) {
  // Basic markdown-ish: bold, bullets, line breaks
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•]\s+/gm, "• ")
    .replace(/\n/g, "<br/>");
}

function showToast(msg, type = "success") {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:${type === "error" ? "#FFEBEE" : "#E8F5E9"};
    border:1px solid ${type === "error" ? "#EF9A9A" : "#A5D6A7"};
    color:${type === "error" ? "#C62828" : "#2E7D32"};
    padding:10px 16px; border-radius:8px;
    font-size:13px; font-weight:500;
    box-shadow:0 4px 12px rgba(0,0,0,.15);
    max-width:340px;
    animation: fadeIn .2s ease;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Init ──────────────────────────────────────────────────────────────────────
refreshDocList();
