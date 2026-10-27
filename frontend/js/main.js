// Main JS Utility for Aadhaar, PAN & Passport Helper

// Detect API base URL
const API_BASE = window.location.origin.includes(":5000") 
  ? window.location.origin 
  : "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initMismatchAnalyzer();
});

// Mobile menu toggle & active link state
function initNavigation() {
  const menuBtn = document.querySelector(".mobile-menu-btn");
  const nav = document.querySelector("nav.main-nav");

  if (menuBtn && nav) {
    menuBtn.addEventListener("click", () => {
      nav.classList.toggle("open");
    });
  }

  // Highlight active link
  const currentPath = window.location.pathname.split("/").pop() || "index.html";
  const links = document.querySelectorAll("nav.main-nav a");
  links.forEach(link => {
    const href = link.getAttribute("href");
    if (href && (href.endsWith(currentPath) || (currentPath === "index.html" && href === "/"))) {
      link.classList.add("active");
    }
  });
}

// Interactive Cross-Document Mismatch Analyzer
function initMismatchAnalyzer() {
  const form = document.getElementById("mismatch-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name10th = document.getElementById("input-10th-name")?.value || "";
    const nameAadhaar = document.getElementById("input-aadhaar-name")?.value || "";
    const namePan = document.getElementById("input-pan-name")?.value || "";
    const dob10th = document.getElementById("input-10th-dob")?.value || "";
    const dobAadhaar = document.getElementById("input-aadhaar-dob")?.value || "";
    const dobPan = document.getElementById("input-pan-dob")?.value || "";

    const btn = form.querySelector("button[type='submit']");
    const resultBox = document.getElementById("mismatch-result");
    
    if (btn) btn.disabled = true;
    if (btn) btn.innerText = "Analyzing Discrepancies...";

    try {
      const resp = await fetch(`${API_BASE}/api/services/analyze-mismatch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name_10th: name10th,
          name_aadhaar: nameAadhaar,
          name_pan: namePan,
          dob_10th: dob10th,
          dob_aadhaar: dobAadhaar,
          dob_pan: dobPan
        })
      });

      const data = await resp.json();
      displayDiagnosisResult(data, resultBox);
    } catch (err) {
      console.warn("Backend API unreachable, using client-side diagnosis fallback:", err);
      // Client-side fallback if backend server isn't running
      const fallbackData = clientSideMismatchAnalysis(name10th, nameAadhaar, namePan, dob10th, dobAadhaar, dobPan);
      displayDiagnosisResult(fallbackData, resultBox);
    } finally {
      if (btn) btn.disabled = false;
      if (btn) btn.innerText = "Run Discrepancy Check";
    }
  });
}

function displayDiagnosisResult(data, resultBox) {
  if (!resultBox) return;

  const badgeClass = data.severity === "High" ? "high" : (data.severity === "Medium" ? "medium" : "none");
  const badgeText = data.is_perfect_match 
    ? "✓ Perfect Match (Zero Risk of Rejection)" 
    : `Risk Level: ${data.severity} Discrepancy`;

  let issuesHtml = "";
  if (data.issues && data.issues.length > 0) {
    issuesHtml = `
      <div style="margin-bottom: 14px;">
        <strong style="color: var(--secondary); font-size: 0.95rem;">Detected Discrepancies:</strong>
        <ul style="margin: 8px 0 0 20px; color: var(--danger);">
          ${data.issues.map(i => `<li style="margin-bottom: 4px;">${i}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  let recsHtml = "";
  if (data.recommendations && data.recommendations.length > 0) {
    recsHtml = `
      <div style="margin-bottom: 14px;">
        <strong style="color: var(--secondary); font-size: 0.95rem;">Recommended Legal Action:</strong>
        <ul style="margin: 8px 0 0 20px; color: #1e3a8a;">
          ${data.recommendations.map(r => `<li style="margin-bottom: 4px;">${r}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  let stepsHtml = "";
  if (data.resolution_steps && data.resolution_steps.length > 0) {
    stepsHtml = `
      <div style="background: white; border: 1px solid var(--border); padding: 14px; border-radius: var(--radius-sm); margin-top: 14px;">
        <strong style="color: var(--secondary); font-size: 0.95rem;">Sequence of Action (Golden Order):</strong>
        <ol style="margin: 8px 0 0 20px; color: var(--text-muted); font-size: 0.9rem;">
          ${data.resolution_steps.map(s => `<li style="margin-bottom: 4px;">${s}</li>`).join("")}
        </ol>
      </div>
    `;
  }

  resultBox.innerHTML = `
    <span class="diagnosis-badge ${badgeClass}">${badgeText}</span>
    ${issuesHtml}
    ${recsHtml}
    ${stepsHtml}
  `;
  resultBox.classList.add("visible");
  resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Client-side fallback if backend API is not yet running
function clientSideMismatchAnalysis(n10, nAadhaar, nPan, d10, dAadhaar, dPan) {
  const norm = str => str.toUpperCase().trim();
  const n1 = norm(n10), nA = norm(nAadhaar), nP = norm(nPan);
  const issues = [];
  const recs = [];
  let sev = "None";

  if (nA && nP && nA !== nP) {
    issues.push(`Aadhaar name ('${nA}') differs from PAN name ('${nP}').`);
    sev = "High";
    recs.push("Update Aadhaar first to match 10th marksheet, then apply for PAN correction.");
  }
  if (n1 && nA && n1 !== nA) {
    issues.push(`10th Marksheet name ('${n1}') differs from Aadhaar ('${nA}').`);
    sev = sev === "High" ? "High" : "Medium";
    recs.push("Aadhaar allows name correction up to 2 times. Update Aadhaar with 10th marksheet as PoI.");
  }
  if (d10 && dAadhaar && d10 !== dAadhaar) {
    issues.push(`Date of birth differs: 10th Certificate (${d10}) vs Aadhaar (${dAadhaar}).`);
    sev = "High";
    recs.push("UIDAI allows DoB update only ONCE. Submit 10th certificate or Birth Certificate immediately.");
  }

  const isMatch = issues.length === 0 && (nA || n1 || nP);
  if (isMatch) {
    recs.push("Records align! You are ready for passport application or e-KYC linking.");
  }

  return {
    is_perfect_match: isMatch,
    severity: isMatch ? "None" : sev,
    issues: issues,
    recommendations: recs,
    resolution_steps: [
      "Step 1: Check 10th Certificate as Anchor proof.",
      "Step 2: Update Aadhaar first at myaadhaar.uidai.gov.in.",
      "Step 3: Update PAN via Protean/UTIITSL.",
      "Step 4: Link PAN with Aadhaar.",
      "Step 5: Apply for Passport without rejection risk."
    ]
  };
}
