// Chatbot UI Controller

document.addEventListener("DOMContentLoaded", () => {
  initChatbot();
});

function initChatbot() {
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const suggestionContainer = document.getElementById("chat-suggestions");

  if (!chatMessages || !chatForm || !chatInput) return;

  // Load starter suggestions
  loadStarterSuggestions(suggestionContainer, chatInput, chatForm);

  // Form submission
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage(chatMessages, "user", query);
    chatInput.value = "";

    // Show typing placeholder
    const typingId = appendTypingIndicator(chatMessages);

    try {
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query })
      });

      removeMessage(typingId);

      if (resp.ok) {
        const json = await resp.json();
        const data = json.data || {};
        appendMessage(chatMessages, "bot", data.answer, data.sources);
        renderSuggestions(suggestionContainer, data.suggestions, chatInput, chatForm);
      } else {
        appendMessage(chatMessages, "bot", "⚠️ We encountered a temporary error connecting to the knowledge assistant. Please try again.");
      }
    } catch (err) {
      removeMessage(typingId);
      console.warn("Using offline bot fallback:", err);
      const fallbackAns = getOfflineAnswer(query);
      appendMessage(chatMessages, "bot", fallbackAns);
    }
  });
}

function appendMessage(container, sender, markdownText, sources = []) {
  const msgEl = document.createElement("div");
  msgEl.className = `message-bubble ${sender}`;

  let parsedHtml = formatMarkdown(markdownText);

  if (sources && sources.length > 0) {
    const sourcesHtml = sources.map(s => `
      <span style="display: inline-block; background: #e2e8f0; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; margin-right: 6px; margin-top: 6px; color: #334155;">
        📄 ${s.title || s.document}
      </span>
    `).join("");
    parsedHtml += `<div style="margin-top: 10px; border-top: 1px solid #e2e8f0; padding-top: 6px;"><strong style="font-size: 0.75rem; color: #64748b;">Grounding Sources:</strong><br>${sourcesHtml}</div>`;
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
  return "Please refer to the official portals for guidance: UIDAI (myaadhaar.uidai.gov.in) for Aadhaar, Protean/Income Tax for PAN, and Passport Seva (passportindia.gov.in) for Passport.";
}
