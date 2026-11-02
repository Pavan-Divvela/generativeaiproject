// Chatbot UI Controller — RAG-powered with service selector & citation rendering

document.addEventListener("DOMContentLoaded", () => {
  initChatbot();
});

function initChatbot() {
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const suggestionContainer = document.getElementById("chat-suggestions");
  const serviceSelect = document.getElementById("service-select");

  if (!chatMessages || !chatForm || !chatInput) return;

  // Load starter suggestions
  loadStarterSuggestions(suggestionContainer, chatInput, chatForm);

  let isSubmitting = false;  // prevent duplicate submissions

  // Form submission
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const query = chatInput.value.trim();
    if (!query) return;

    const selectedService = serviceSelect ? serviceSelect.value : "";

    isSubmitting = true;
    chatInput.disabled = true;

    appendMessage(chatMessages, "user", query);
    chatInput.value = "";

    // Show typing placeholder
    const typingId = appendTypingIndicator(chatMessages);

    try {
      const body = { message: query };
      if (selectedService) body.service = selectedService;

      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      removeMessage(typingId);

      if (resp.ok) {
        const json = await resp.json();
        const data = json.data || {};
        appendMessage(chatMessages, "bot", data.answer, data.sources || [], data.source_mode);
        renderSuggestions(suggestionContainer, data.suggestions, chatInput, chatForm);
      } else {
        const errJson = await resp.json().catch(() => ({}));
        appendMessage(chatMessages, "bot",
          `⚠️ ${errJson.message || "We encountered a temporary error. Please try again."}`);
      }
    } catch (err) {
      removeMessage(typingId);
      console.warn("Using offline bot fallback:", err);
      const fallbackAns = getOfflineAnswer(query);
      appendMessage(chatMessages, "bot", fallbackAns);
    } finally {
      isSubmitting = false;
      chatInput.disabled = false;
      chatInput.focus();
    }
  });
}

function appendMessage(container, sender, markdownText, sources = [], sourceMode = "") {
  const msgEl = document.createElement("div");
  msgEl.className = `message-bubble ${sender}`;

  let parsedHtml = formatMarkdown(markdownText || "");

  // ── Citations / Sources ─────────────────────────────────────────────────────
  if (sources && sources.length > 0) {
    const sourcesHtml = sources.map((s, i) => {
      const label = s.title || s.document || "Official Document";
      const page  = s.page_range ? ` · ${s.page_range}` : "";
      const svc   = s.service ? ` [${s.service.toUpperCase()}]` : "";

      if (s.official_url) {
        return `
          <a href="${s.official_url}" target="_blank" rel="noopener noreferrer"
             style="display:inline-flex; align-items:center; gap:6px; background:#dbeafe;
                    color:#1e40af; font-size:0.75rem; padding:3px 10px; border-radius:12px;
                    margin:3px 4px 0 0; text-decoration:none; font-weight:600;">
            📄 ${label}${svc}${page} ↗
          </a>`;
      } else {
        return `
          <span style="display:inline-block; background:#e2e8f0; font-size:0.75rem;
                       padding:3px 10px; border-radius:12px; margin:3px 4px 0 0; color:#334155;">
            📄 ${label}${svc}${page}
          </span>`;
      }
    }).join("");

    const modeLabel = sourceMode === "chroma_rag"
      ? "🔍 RAG Sources (Official PDFs)"
      : "📚 Knowledge Base Sources";

    parsedHtml += `
      <div style="margin-top:10px; border-top:1px solid #e2e8f0; padding-top:8px;">
        <strong style="font-size:0.72rem; color:#64748b; display:block; margin-bottom:4px;">
          ${modeLabel}:
        </strong>
        <div>${sourcesHtml}</div>
      </div>`;
  }

  msgEl.innerHTML = parsedHtml;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator(container) {
  const id = `typing-${Date.now()}`;
  const typingEl = document.createElement("div");
  typingEl.id = id;
  typingEl.className = "message-bubble bot";
  typingEl.innerHTML = `<em>Consulting official guidelines...</em>`;
  container.appendChild(typingEl);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function renderSuggestions(container, suggestions, inputEl, formEl) {
  if (!container || !suggestions || suggestions.length === 0) return;
  container.innerHTML = "";

  suggestions.forEach(text => {
    const chip = document.createElement("button");
    chip.className = "chip-btn";
    chip.innerText = text;
    chip.addEventListener("click", () => {
      inputEl.value = text;
      formEl.dispatchEvent(new Event("submit"));
    });
    container.appendChild(chip);
  });
}

async function loadStarterSuggestions(container, inputEl, formEl) {
  if (!container) return;
  try {
    const resp = await fetch(`${API_BASE}/api/chat/suggestions`);
    if (resp.ok) {
      const data = await resp.json();
      renderSuggestions(container, data.suggestions, inputEl, formEl);
      return;
    }
  } catch (err) {
    // Offline starter suggestions
  }
  renderSuggestions(container, [
    "How to link PAN with Aadhaar after paying the ₹1,000 penalty?",
    "What documents are required for a Tatkaal passport?",
    "How to resolve name mismatch between 10th marksheet and Aadhaar?",
    "What is Non-ECR status in Indian passport?"
  ], inputEl, formEl);
}

// Simple markdown formatter
function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, '<h4 style="color: #1e3a8a; margin: 10px 0 6px 0; font-size: 1.05rem;">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 style="color: #0f172a; margin: 12px 0 8px 0; font-size: 1.15rem;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener" style="color: #2563eb; text-decoration: underline;">$1</a>')
    .replace(/\n\n/gim, '<p style="margin-bottom: 8px;"></p>')
    .replace(/\n\* (.*)/gim, '<li style="margin-left: 20px;">$1</li>')
    .replace(/\n([0-9]+)\. (.*)/gim, '<li style="margin-left: 20px;">$2</li>');

  return html;
}

function getOfflineAnswer(query) {
  const q = query.toLowerCase();
  if (q.includes("pan") && q.includes("aadhaar")) {
    return "To link PAN with Aadhaar:\n1. Pay the ₹1,000 penalty on the Income Tax e-filing portal under Minor Head 500.\n2. Wait 24 to 48 hours for Challan clearance.\n3. Return to 'Link Aadhaar' page and verify OTP.";
  }
  if (q.includes("tatkaal")) {
    return "Tatkaal passport requires 3 identity documents from the approved list (e.g., Aadhaar + PAN + Voter ID) with 100% identical names and birth dates. Fee is ₹3,500 (36 pages) or ₹4,000 (60 pages).";
  }
  return "Please refer to the official portals for guidance: UIDAI (myaadhaar.uidai.gov.in) for Aadhaar, Income Tax for PAN, and Passport Seva (passportindia.gov.in) for Passport.";
}
