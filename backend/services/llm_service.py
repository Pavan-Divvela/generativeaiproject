import os
import json
import re
import requests
from config import Config

def get_api_key() -> str:
    """Retrieves Gemini API key from environment or Config."""
    return os.getenv("GEMINI_API_KEY", "").strip() or getattr(Config, "GEMINI_API_KEY", "").strip()

def query_gemini_api(prompt: str, api_key: str) -> str:
    """Invokes Gemini REST API to answer queries with grounding."""
    # Active model for Gemini API key
    primary_model = "gemini-3-flash-preview"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1000
        }
    }

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{primary_model}:generateContent?key={api_key}"
        resp = requests.post(url, headers=headers, json=payload, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "").strip()
                    if text:
                        return text
    except Exception:
        # Fallback to local domain RAG engine
        pass

    return ""

def synthesize_rag_response(query: str, retrieved_chunks: list) -> str:
    """
    Intelligent domain synthesis engine. Combines user query and retrieved 
    knowledge-base context into an authoritative, structured markdown answer.
    """
    clean_q = query.lower()
    api_key = get_api_key()

    # Build context string
    context_text = "\n\n".join([f"### {c.get('title', 'Document Excerpt')}\n{c.get('content', '')}" for c in retrieved_chunks[:3]])

    # 1. Try Gemini API first if API key is present
    if api_key:
        system_prompt = (
            "You are the Official Indian Identity Document Assistant (Aadhaar, PAN, Passport).\n"
            "Answer the user query accurately, politely, and comprehensively using the provided official guidelines.\n"
            "Format your answer with clear markdown headers, bold bullet points, and practical warnings.\n\n"
            f"Knowledge Base Guidelines:\n{context_text}\n\n"
            f"User Question: {query}"
        )
        api_result = query_gemini_api(system_prompt, api_key)
        if api_result:
            return api_result

    # 2. Comprehensive Domain Expert Engine (Offline & Fallback Mode)
    response_parts = []

    # A. PAN Card Queries
    if "pan" in clean_q:
        if any(w in clean_q for w in ["apply", "document", "documents", "need", "needed", "require", "required", "new", "fresh", "get"]):
            response_parts.append("### 💳 Documents Required to Apply for a PAN Card")
            response_parts.append(
                "To apply for a new PAN card (Form 49A / Instant e-PAN), Indian citizens need to submit three standard proofs. "
                "**Aadhaar Card alone is sufficient** for all three if it contains your full Date of Birth."
            )
            response_parts.append(
                "**1. Proof of Identity (PoI) - Any ONE:**\n"
                "* **Aadhaar Card** (Most recommended)\n"
                "* Voter ID (EPIC Card)\n"
                "* Passport\n"
                "* Driving Licence\n"
                "* Ration Card with applicant's photograph\n\n"
                "**2. Proof of Address (PoA) - Any ONE:**\n"
                "* **Aadhaar Card**\n"
                "* Electricity / Water / Piped Gas Bill (less than 3 months old)\n"
                "* Bank Account Passbook or Statement (with branch stamp)\n"
                "* Registered Rent Agreement\n\n"
                "**3. Proof of Date of Birth (PoB) - Any ONE:**\n"
                "* Birth Certificate issued by Municipal Authority\n"
                "* Matriculation (10th Standard) Certificate / Marksheet\n"
                "* Aadhaar Card (must show complete DD/MM/YYYY date)\n"
                "* Passport or Driving Licence\n\n"
                "**Application Options:**\n"
                "* **Instant e-PAN (Free):** Generated in 10 minutes on the Income Tax e-Filing portal via Aadhaar OTP.\n"
                "* **Physical PAN Card (₹107):** Applied via Protean (NSDL) or UTIITSL; plastic card delivered to your doorstep."
            )
        elif any(w in clean_q for w in ["link", "penalty", "fee", "how to link", "1000", "challan"]):
            response_parts.append("### 🔗 How to Link PAN with Aadhaar (Step-by-Step)")
            response_parts.append(
                "Under Section 139AA and Section 234H of the Income Tax Act, linking PAN with Aadhaar is mandatory for all taxpayers.\n\n"
                "**Procedure:**\n"
                "1. **Check Status First:** Go to the [Income Tax e-Filing Portal](https://eportal.incometax.gov.in/iec/foservices/#/pre-login/link-aadhaar-status) to confirm if already linked.\n"
                "2. **Pay ₹1,000 Late Fee:** Under *e-Pay Tax*, select the **Income Tax** tile, Assessment Year (Current), and Type of Payment as **Minor Head 500 ('Other Receipts / Fee for linking')**.\n"
                "3. **Wait for Challan Sync:** Wait 24 to 48 hours for the payment to clear in the tax database.\n"
                "4. **Complete Linking:** Return to 'Link Aadhaar', enter PAN & Aadhaar, and verify via Aadhaar OTP."
            )
        elif any(w in clean_q for w in ["mismatch", "fail", "error", "different"]):
            response_parts.append("### ⚠️ Resolving PAN-Aadhaar Demographic Mismatch")
            response_parts.append(
                "PAN-Aadhaar linking fails when Name, Date of Birth, or Gender differs between UIDAI and Income Tax databases. "
                "The Income Tax Department strictly prohibits single initials (e.g. *R. Sharma*), requiring full expanded names (*Ramesh Sharma*).\n\n"
                "**Resolution Order:**\n"
                "* Treat your **10th Class Marksheet / Birth Certificate** as the master anchor proof.\n"
                "* If Aadhaar has initials, update Aadhaar first to the full expanded name.\n"
                "* Once Aadhaar is updated, update PAN via Form 49A Changes/Correction.\n"
                "* Once both match 100%, submit the linking request."
            )
        else:
            response_parts.append("### 💳 PAN Card Overview & Services")
            response_parts.append(
                "PAN (Permanent Account Number) is a 10-digit alphanumeric identifier issued by the Income Tax Department.\n\n"
                "* **Instant e-PAN:** Free, paperless, issued in 10-30 minutes using Aadhaar e-KYC.\n"
                "* **Physical PAN (Form 49A):** ₹107 fee, dispatched to your address by Speed Post.\n"
                "* **Reprint Physical Card:** If you have an e-PAN, order a physical plastic card for ₹50 from Protean (NSDL) or UTIITSL."
            )

    # B. Passport Queries
    elif "passport" in clean_q:
        if any(w in clean_q for w in ["tatkaal", "urgent", "emergency", "fast"]):
            response_parts.append("### ⚡ Tatkaal Passport Scheme (Urgent Issuance)")
            response_parts.append(
                "The Tatkaal scheme allows passport dispatch within 1 to 3 working days by deferring police verification until after issuance.\n\n"
                "**Key Requirements:**\n"
                "* **Fee:** ₹3,500 (36 pages) or ₹4,000 (60 pages jumbo booklet).\n"
                "* **3 Mandatory Proofs:** Must submit 3 distinct documents from the approved list (e.g., Aadhaar + PAN + Voter ID / Driving Licence).\n"
                "* **Zero Mismatch Rule:** Names and Date of Birth must match 100% identically across all documents. Any discrepancy causes immediate downgrade to Normal scheme."
            )
        elif any(w in clean_q for w in ["non-ecr", "ecr", "emigration", "10th", "matriculation"]):
            response_parts.append("### 🛂 Non-ECR Status (Emigration Check Not Required)")
            response_parts.append(
                "Non-ECR status allows Indian citizens to travel abroad for employment to 18 designated countries without needing clearance from the Protector of Emigrants (PoE).\n\n"
                "**Who Qualifies:**\n"
                "* Any applicant who has passed **10th Standard (Matriculation)** or higher education.\n"
                "* Individual Income Taxpayers who have paid tax in their personal capacity.\n"
                "* Persons aged 50 years and above.\n"
                "* Children below 18 years of age."
            )
        elif any(w in clean_q for w in ["police", "verification", "pcc"]):
            response_parts.append("### 👮 Passport Police Verification Readiness")
            response_parts.append(
                "Police verification verifies your address and Indian citizenship.\n\n"
                "**Checklist for Police Visit:**\n"
                "* Original Aadhaar card & current address proof (Electricity bill, bank passbook, or Registered Rent Agreement).\n"
                "* 2 neighbor references living in the same locality with their Aadhaar copies and phone numbers.\n"
                "* Self-attested copies of 10th marksheet and PAN card."
            )
        else:
            response_parts.append("### 🛂 Documents Required for Fresh Passport (Normal Scheme)")
            response_parts.append(
                "For an adult applying under Normal Scheme (Fee: ₹1,500 for 36 pages / ₹2,000 for 60 pages):\n\n"
                "**1. Proof of Present Address (PoA):**\n"
                "* Aadhaar Card / e-Aadhaar (DigiLocker / Color Print)\n"
                "* Bank Passbook with applicant photo and branch stamp\n"
                "* Electricity Bill or Water Bill (within last 3 months)\n"
                "* **Registered Rent Agreement** (Unregistered notary agreements are rejected)\n\n"
                "**2. Proof of Date of Birth (PoB):**\n"
                "* Birth Certificate issued by Municipal Corporation\n"
                "* 10th Standard / Matriculation Pass Certificate\n"
                "* Aadhaar Card with full DD/MM/YYYY\n\n"
                "**3. Non-ECR Proof:** 10th Standard pass marksheet or degree certificate."
            )

    # C. Aadhaar Queries
    elif "aadhaar" in clean_q:
        if any(w in clean_q for w in ["update", "change", "correct", "correction"]):
            response_parts.append("### 🆔 Aadhaar Demographic & Biometric Updates")
            response_parts.append(
                "UIDAI enforces strict lifetime limits to protect personal identity:\n\n"
                "* **Name Change:** Allowed only **2 times** in a lifetime (Requires 10th marksheet, Passport, or Gazette notification).\n"
                "* **Date of Birth:** Allowed only **1 time** in a lifetime (Requires Birth Certificate or Board Marksheet).\n"
                "* **Gender:** Allowed only **1 time**.\n"
                "* **Address:** Unlimited updates online using valid PoA or Head of Family (HoF) consent.\n"
                "* **Fee:** ₹50 for demographic update; ₹100 for adult biometric update."
            )
        elif any(w in clean_q for w in ["child", "minor", "5", "15", "biometric"]):
            response_parts.append("### 👶 Mandatory Biometric Updates for Children (MBU)")
            response_parts.append(
                "UIDAI mandates that all children must update their fingerprints, iris scans, and facial photograph at:\n\n"
                "* **Age 5** (Transition from Baal Aadhaar to standard Aadhaar)\n"
                "* **Age 15** (Final adult biometric capture)\n\n"
                "**Important:** Both mandatory childhood biometric updates (Age 5 and Age 15) are **100% FREE** of cost at all authorized Aadhaar Seva Kendras."
            )
        else:
            response_parts.append("### 🆔 Aadhaar Enrollment & Acceptable Documents")
            response_parts.append(
                "Fresh Aadhaar enrollment is completely free of charge at any authorized Kendra.\n\n"
                "**Documents Required:**\n"
                "* **Proof of Identity (PoI):** Voter ID, PAN Card, Passport, Ration Card with photo, Driving Licence.\n"
                "* **Proof of Address (PoA):** Electricity/Water Bill, Bank Passbook, Registered Rent Agreement.\n"
                "* **Proof of Date of Birth (PoB):** Birth Certificate or 10th Board Certificate."
            )

    # D. Name Mismatch & Discrepancies
    elif any(w in clean_q for w in ["name", "spelling", "mismatch", "discrepancy", "initial", "surname", "affidavit", "gazette"]):
        response_parts.append("### ⚠️ Name & Document Discrepancy Resolution")
        response_parts.append(
            "When personal details differ across records, follow the legal hierarchy:\n\n"
            "1. **Anchor Document:** 10th Board Certificate or Birth Certificate is legally supreme.\n"
            "2. **Aadhaar First:** Always update Aadhaar first to match your 10th certificate.\n"
            "3. **PAN Second:** Update PAN via Form 49A using your corrected Aadhaar.\n"
            "4. **Passport Last:** Apply for Passport only after Aadhaar and PAN match.\n\n"
            "* **Single Name on Passport:** Having only one name (e.g. *Pooja*) causes visa issues (FNU). Add a surname on Aadhaar before applying for passport.\n"
            "* **Marriage Surname Change:** Women changing surname after marriage do NOT strictly need a marriage certificate for passport; a self-declaration in **Annexure D** is accepted."
        )

    # E. General Fallback grounded on Retrieved RAG Chunks
    else:
        if retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            response_parts.append(f"### 📋 {top_chunk.get('title', 'Document Process Guide')}")
            response_parts.append(top_chunk.get('content', ''))
            if len(retrieved_chunks) > 1:
                second = retrieved_chunks[1]
                response_parts.append(f"\n\n**Additional Guidance ({second.get('title', 'Reference')}):**\n{second.get('body', '')[:300]}...")
        else:
            response_parts.append(
                "### 🇮🇳 Identity Document Guidance\n"
                "I can guide you through Indian identity document processes:\n\n"
                "* **PAN Card:** Applying for instant e-PAN, Form 49A, and PAN-Aadhaar linking.\n"
                "* **Aadhaar:** Demographic corrections, mandatory childhood biometrics, and acceptable proofs.\n"
                "* **Passport:** Normal vs. Tatkaal schemes, Non-ECR status, and police verification readiness.\n"
                "* **Discrepancies:** Name mismatches, initial expansion, and affidavit requirements."
            )

    # Append official government portals footer
    response_parts.append("\n---\n**Official Government Portals:**")
    response_parts.append("* Aadhaar (UIDAI): [myaadhaar.uidai.gov.in](https://myaadhaar.uidai.gov.in/)")
    response_parts.append("* PAN (Income Tax): [eportal.incometax.gov.in](https://eportal.incometax.gov.in/)")
    response_parts.append("* Passport Seva (MEA): [passportindia.gov.in](https://www.passportindia.gov.in/)")

    return "\n\n".join(response_parts)
