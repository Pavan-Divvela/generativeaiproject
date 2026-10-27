// Interactive Checklist Manager

document.addEventListener("DOMContentLoaded", () => {
  initChecklistWizard();
});

function initChecklistWizard() {
  const form = document.getElementById("checklist-wizard-form");
  const outputContainer = document.getElementById("checklist-output");
  if (!form || !outputContainer) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const targetService = document.getElementById("wizard-service").value;
    const ageGroup = document.getElementById("wizard-age")?.value || "adult";
    const has10th = document.getElementById("wizard-has-10th")?.checked ?? true;
    const scheme = document.getElementById("wizard-scheme")?.value || "normal";
    const isGovt = document.getElementById("wizard-govt")?.checked ?? false;

    const btn = form.querySelector("button[type='submit']");
    if (btn) btn.innerText = "Generating Checklist...";

    try {
      const resp = await fetch(`${API_BASE}/api/checklist/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_service: targetService,
          age_group: ageGroup,
          has_10th: has10th,
          scheme: scheme,
          is_employed_govt: isGovt
        })
      });

      const json = await resp.json();
      renderChecklist(json.data, outputContainer);
    } catch (err) {
      console.warn("Using offline checklist generator fallback:", err);
      const fallbackData = getOfflineChecklist(targetService, scheme, has10th);
      renderChecklist(fallbackData, outputContainer);
    } finally {
      if (btn) btn.innerText = "Generate My Custom Checklist";
    }
  });
}

function renderChecklist(data, container) {
  const storageKey = `checklist_${data.target_service}`;
  const savedState = JSON.parse(localStorage.getItem(storageKey) || "{}");

  const docs = data.mandatory_documents || [];
  
  let docsHtml = docs.map((doc, idx) => {
    const isChecked = !!savedState[idx];
    return `
      <div class="checklist-item ${isChecked ? 'checked' : ''}" data-idx="${idx}">
        <input type="checkbox" id="doc-${idx}" ${isChecked ? 'checked' : ''} onchange="toggleDocCheck('${storageKey}', ${idx}, this)">
        <div style="flex: 1;">
          <label for="doc-${idx}" class="item-title" style="cursor: pointer; font-weight: 600; display: block; color: var(--secondary);">
            ${doc.name}
          </label>
          <span style="font-size: 0.85rem; color: var(--text-muted);">${doc.desc} (${doc.type})</span>
        </div>
      </div>
    `;
  }).join("");

  const notesHtml = (data.notes || []).map(n => `<li style="margin-bottom: 6px;">${n}</li>`).join("");

  container.innerHTML = `
    <div style="background: white; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 24px; margin-top: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h3 style="color: var(--secondary); font-size: 1.3rem;">Your Personalized Document Checklist</h3>
          <p style="color: var(--text-muted); font-size: 0.9rem;">Bring original physical documents + 2 self-attested photocopies.</p>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-outline" onclick="window.print()">🖨️ Print / Save PDF</button>
          ${data.official_url ? `<a href="${data.official_url}" target="_blank" rel="noopener" class="btn btn-primary">Go to Official Portal ↗</a>` : ''}
        </div>
      </div>

      <div style="display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap;">
        <div style="background: #f1f5f9; padding: 10px 16px; border-radius: var(--radius-sm); font-size: 0.9rem;">
          <strong>Estimated Official Fee:</strong> <span style="color: var(--primary); font-weight: 700;">${data.estimated_fee}</span>
        </div>
        <div style="background: #f1f5f9; padding: 10px 16px; border-radius: var(--radius-sm); font-size: 0.9rem;">
          <strong>Expected Timeline:</strong> <span style="color: var(--primary); font-weight: 700;">${data.estimated_time}</span>
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h4 style="margin-bottom: 12px; color: var(--secondary);">Required Original Documents:</h4>
        ${docsHtml}
      </div>

      ${notesHtml ? `
        <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 16px; border-radius: var(--radius-sm);">
          <strong style="color: #b45309; font-size: 0.9rem;">⚠️ Critical Submission Warnings:</strong>
          <ul style="margin: 8px 0 0 20px; color: #92400e; font-size: 0.85rem;">
            ${notesHtml}
          </ul>
        </div>
      ` : ''}
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

window.toggleDocCheck = function(storageKey, idx, checkbox) {
  const item = checkbox.closest(".checklist-item");
  if (item) {
    item.classList.toggle("checked", checkbox.checked);
  }
  const savedState = JSON.parse(localStorage.getItem(storageKey) || "{}");
  savedState[idx] = checkbox.checked;
  localStorage.setItem(storageKey, JSON.stringify(savedState));
};

function getOfflineChecklist(service, scheme, has10th) {
  if (service.includes("pan")) {
    return {
      target_service: service,
      estimated_fee: "₹107 (Physical) / Free (Instant e-PAN)",
      estimated_time: "10 min (e-PAN) to 15 days (Physical)",
      official_url: "https://www.onlineservices.nsdl.com/",
      mandatory_documents: [
        { name: "Aadhaar Card", desc: "Proof of Identity & Address", type: "PoI/PoA" },
        { name: "10th Marksheet or Birth Certificate", desc: "Proof of Date of Birth", type: "PoB" },
        { name: "2 Passport Size Photos", desc: "White background, for physical card", type: "Photo" }
      ],
      notes: ["Ensure full name matches 10th certificate to avoid PAN-Aadhaar linking errors."]
    };
  }
  return {
    target_service: service,
    estimated_fee: scheme === "tatkaal" ? "₹3,500" : "₹1,500",
    estimated_time: scheme === "tatkaal" ? "1 - 3 days" : "15 - 30 days",
    official_url: "https://www.passportindia.gov.in/",
    mandatory_documents: [
      { name: "Aadhaar Card / e-Aadhaar", desc: "Present Address & Identity", type: "PoA/PoI" },
      { name: "10th Standard / Matriculation Certificate", desc: "Date of Birth & Non-ECR status", type: "PoB/Non-ECR" },
      { name: "PAN Card", desc: "Secondary photo identity", type: "PoI" }
    ],
    notes: ["All photocopies must be self-attested with signature and date."]
  };
}
