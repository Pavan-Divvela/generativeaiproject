import re
from database.db import query_db

def normalize_name(name: str) -> str:
    """Cleans and standardizes name string for comparison."""
    if not name:
        return ""
    # Strip titles like Shri, Smt, Mr, Mrs, Dr
    name = re.sub(r'^(mr|mrs|ms|shri|smt|dr|master)\.?\s+', '', name.strip(), flags=re.IGNORECASE)
    # Remove excessive whitespace and special characters except dots
    name = re.sub(r'[^a-zA-Z\s\.]', '', name)
    return ' '.join(name.upper().split())

def analyze_name_discrepancy(name_10th: str, name_aadhaar: str, name_pan: str, dob_10th: str = "", dob_aadhaar: str = "", dob_pan: str = ""):
    """
    Performs comprehensive cross-document name & DOB comparison.
    Generates actionable legal guidance for alignment.
    """
    norm_10th = normalize_name(name_10th)
    norm_aadhaar = normalize_name(name_aadhaar)
    norm_pan = normalize_name(name_pan)

    issues = []
    recommendations = []
    severity = "Low"
    affidavit_required = False
    gazette_required = False

    def elevate_severity(current, new_sev):
        levels = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
        if levels.get(new_sev, 0) > levels.get(current, 0):
            return new_sev
        return current

    # Check 1: Single Name Detection
    for doc_name, val in [("10th Certificate", norm_10th), ("Aadhaar", norm_aadhaar), ("PAN", norm_pan)]:
        if val and " " not in val:
            issues.append(f"Single name detected on {doc_name} ('{val}'). Passports and international visas mandate separate Given Name and Surname.")
            severity = elevate_severity(severity, "High")
            recommendations.append(f"Add a surname or father's name on Aadhaar before proceeding with Passport application.")

    # Check 2: Initial vs Expanded Name (e.g. 'R. SHARMA' vs 'RAMESH SHARMA')
    has_initial_aadhaar = any(len(part) == 1 or part.endswith('.') for part in norm_aadhaar.split())
    has_initial_pan = any(len(part) == 1 or part.endswith('.') for part in norm_pan.split())
    
    if has_initial_aadhaar and not has_initial_pan and norm_pan:
        issues.append(f"Aadhaar has initials ('{norm_aadhaar}') whereas PAN has expanded name ('{norm_pan}'). Income Tax system does not permit initials, causing PAN-Aadhaar linking failure.")
        severity = elevate_severity(severity, "High")
        recommendations.append("First update Aadhaar with full expanded name using 10th certificate as proof. After Aadhaar is updated, complete PAN-Aadhaar linking.")

    # Check 3: Name Mismatch between 10th & Aadhaar
    if norm_10th and norm_aadhaar and norm_10th != norm_aadhaar:
        tokens_10th = set(norm_10th.replace('.', '').split())
        tokens_aadhaar = set(norm_aadhaar.replace('.', '').split())
        
        if tokens_10th == tokens_aadhaar:
            issues.append(f"Word order difference between 10th Marksheet ('{norm_10th}') and Aadhaar ('{norm_aadhaar}').")
            severity = elevate_severity(severity, "Medium")
            recommendations.append("Reorder name in Aadhaar to match 10th certificate order (Given Name followed by Surname).")
        elif len(tokens_10th.intersection(tokens_aadhaar)) > 0:
            issues.append(f"Partial spelling or token discrepancy between 10th Certificate ('{norm_10th}') and Aadhaar ('{norm_aadhaar}').")
            severity = elevate_severity(severity, "Medium")
            recommendations.append("Update Aadhaar name to match your 10th marksheet. UIDAI allows name change up to 2 times.")
        else:
            issues.append(f"Major name mismatch between 10th Certificate ('{norm_10th}') and Aadhaar ('{norm_aadhaar}').")
            severity = elevate_severity(severity, "High")
            affidavit_required = True
            gazette_required = True
            recommendations.append("Major name difference requires a Gazette Notification publication, newspaper announcements, and a notarized affidavit.")

    # Check 4: Date of Birth Mismatch
    dob_issues = []
    if dob_10th and dob_aadhaar and dob_10th != dob_aadhaar:
        dob_issues.append(f"DoB differs: 10th Certificate ({dob_10th}) vs Aadhaar ({dob_aadhaar}).")
        severity = "High"
        recommendations.append("Update Aadhaar DoB immediately using 10th marksheet / Birth Certificate. Note: UIDAI permits DoB update only ONCE in a lifetime.")
    
    if dob_aadhaar and dob_pan and dob_aadhaar != dob_pan:
        dob_issues.append(f"DoB differs: Aadhaar ({dob_aadhaar}) vs PAN ({dob_pan}). This will block PAN-Aadhaar linking.")
        severity = "High"
        recommendations.append("Apply for PAN correction (Form 49A Changes) using updated Aadhaar as Proof of Date of Birth.")

    # Check 5: Perfect Match
    all_entered = [n for n in [norm_10th, norm_aadhaar, norm_pan] if n]
    is_perfect_match = len(all_entered) > 1 and len(set(all_entered)) == 1 and not dob_issues

    if is_perfect_match:
        severity = "None"
        recommendations.append("All personal records match perfectly! You are 100% eligible to apply for Passport, link PAN-Aadhaar, or undergo paperless e-KYC.")

    # Fallback if no issues identified but fields partially filled
    if not issues and not dob_issues and not is_perfect_match:
        recommendations.append("Ensure your full name across all documents strictly follows the spelling on your 10th Certificate or Birth Certificate.")

    return {
        "status": "success",
        "is_perfect_match": is_perfect_match,
        "severity": severity,
        "normalized": {
            "name_10th": norm_10th,
            "name_aadhaar": norm_aadhaar,
            "name_pan": norm_pan
        },
        "issues": issues + dob_issues,
        "recommendations": recommendations,
        "affidavit_required": affidavit_required,
        "gazette_required": gazette_required,
        "resolution_steps": [
            "Step 1: Treat 10th Board Certificate / Birth Certificate as the Master Anchor.",
            "Step 2: Update Aadhaar first (if different from 10th cert) at myaadhaar.uidai.gov.in.",
            "Step 3: Update PAN through Protean / UTIITSL using updated Aadhaar.",
            "Step 4: Once Aadhaar & PAN match, link them on the Income Tax e-Filing portal.",
            "Step 5: Apply for Passport at passportindia.gov.in with zero risk of rejection."
        ]
    }

def generate_checklist(target_service: str, age_group: str = "adult", has_10th: bool = True, scheme: str = "normal", is_employed_govt: bool = False):
    """
    Generates a personalized, bulletproof document checklist and fee estimate.
    """
    checklist = {
        "target_service": target_service,
        "mandatory_documents": [],
        "optional_documents": [],
        "estimated_fee": "₹0",
        "estimated_time": "Varies",
        "official_url": "",
        "notes": []
    }

    if target_service.startswith("aadhaar"):
        checklist["official_url"] = "https://myaadhaar.uidai.gov.in/"
        if "fresh" in target_service:
            checklist["estimated_fee"] = "Free"
            checklist["estimated_time"] = "15 - 30 days"
            checklist["mandatory_documents"] = [
                {"type": "PoI", "name": "Voter ID / PAN Card / 10th Marksheet / School ID", "desc": "Any approved photo identity"},
                {"type": "PoA", "name": "Electricity Bill / Bank Passbook / Registered Rent Agreement", "desc": "Present residential address proof"},
                {"type": "PoB", "name": "Birth Certificate or 10th School Leaving Certificate", "desc": "Showing full DD/MM/YYYY date"}
            ]
            checklist["notes"] = [
                "Biometrics (10 fingerprints, both iris, face photo) will be captured at the Aadhaar center.",
                "Original documents must be brought along; they will be scanned and returned immediately."
            ]
        else: # Update
            checklist["estimated_fee"] = "₹50 (Online/Offline) or ₹100 (Biometric)"
            checklist["estimated_time"] = "5 - 15 days"
            checklist["mandatory_documents"] = [
                {"type": "Existing Proof", "name": "Current Aadhaar Number & Linked Mobile for OTP", "desc": "For online verification"},
                {"type": "Supporting Proof", "name": "PoI for Name change, PoA for Address, Birth Cert for DoB", "desc": "Valid supporting original proof"}
            ]

    elif target_service.startswith("pan"):
        if "instant" in target_service:
            checklist["official_url"] = "https://eportal.incometax.gov.in/iec/foservices/#/pre-login/instant-e-pan"
            checklist["estimated_fee"] = "Free"
            checklist["estimated_time"] = "10 - 30 minutes"
            checklist["mandatory_documents"] = [
                {"type": "Primary", "name": "Aadhaar Card with full DoB", "desc": "Aadhaar must not be linked to any prior PAN"},
                {"type": "Mobile", "name": "Aadhaar-Linked Active Mobile Number", "desc": "To receive e-KYC OTP"}
            ]
            checklist["notes"] = [
                "Paperless instant generation. You will receive a digitally signed PDF PAN.",
                "Physical plastic card can be ordered later for ₹50 from Protean or UTIITSL."
            ]
        elif "link" in target_service:
            checklist["official_url"] = "https://eportal.incometax.gov.in/iec/foservices/#/pre-login/bl-link-aadhaar"
            checklist["estimated_fee"] = "₹1,000 (Late fee under Section 234H)"
            checklist["estimated_time"] = "2 - 5 days after payment clearance"
            checklist["mandatory_documents"] = [
                {"type": "PAN", "name": "10-digit PAN Card Number", "desc": "Active or inoperative PAN"},
                {"type": "Aadhaar", "name": "12-digit Aadhaar Number", "desc": "Demographics must match PAN"},
                {"type": "Challan", "name": "Challan Payment Receipt (Minor Head 500)", "desc": "Paid through e-Pay Tax"}
            ]
        else: # Physical PAN 49A
            checklist["official_url"] = "https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html"
            checklist["estimated_fee"] = "₹107 (India) / ₹1,017 (Foreign)"
            checklist["estimated_time"] = "10 - 20 days"
            checklist["mandatory_documents"] = [
                {"type": "PoI", "name": "Aadhaar Card / Voter ID / Passport", "desc": "Identity proof"},
                {"type": "PoA", "name": "Aadhaar Card / Bank Passbook / Utility Bill", "desc": "Address proof"},
                {"type": "PoB", "name": "Aadhaar Card / 10th Certificate / Birth Certificate", "desc": "Date of Birth proof"},
                {"type": "Photos", "name": "2 Recent Passport Size Colored Photographs", "desc": "3.5 cm x 2.5 cm white background"}
            ]

    elif target_service.startswith("passport"):
        checklist["official_url"] = "https://www.passportindia.gov.in/"
        is_tatkaal = scheme.lower() == "tatkaal" or "tatkaal" in target_service
        
        checklist["estimated_fee"] = "₹3,500 (36 pages) / ₹4,000 (60 pages)" if is_tatkaal else "₹1,500 (36 pages) / ₹2,000 (60 pages)"
        checklist["estimated_time"] = "1 - 3 working days (Post-police verification)" if is_tatkaal else "15 - 30 working days"

        docs = [
            {"type": "PoA (Present Address)", "name": "Aadhaar Card / e-Aadhaar / Bank Passbook", "desc": "Must reflect current residence for at least 1 year"},
            {"type": "PoB (Date of Birth)", "name": "Birth Certificate or 10th Matriculation Certificate", "desc": "Supreme proof of birth date"},
            {"type": "PoI (Identity)", "name": "PAN Card / Voter ID / Driving Licence", "desc": "Photo identification document"}
        ]

        if has_10th:
            docs.append({
                "type": "Non-ECR Proof",
                "name": "10th Standard / Matriculation Pass Certificate",
                "desc": "Eliminates Emigration Check Required stamp for overseas employment"
            })
        
        if is_tatkaal:
            docs.append({
                "type": "Tatkaal Requirement",
                "name": "3 Distinct Identity Documents from Approved 16-Doc List",
                "desc": "e.g., Aadhaar + PAN + Voter ID (Names must match 100%)"
            })

        if is_employed_govt:
            docs.append({
                "type": "Government Employee",
                "name": "No Objection Certificate (NOC) / Prior Intimation Letter (Annexure H/M)",
                "desc": "Mandatory for PSU / Central / State Government employees"
            })

        checklist["mandatory_documents"] = docs
        checklist["notes"] = [
            "All applicants must bring original documents along with 2 sets of self-attested photocopies to PSK.",
            "Adult photograph is captured digitally at Counter A of PSK.",
            "If using a rent agreement for address proof, it MUST be a Registered Rent Agreement; unregistered notary agreements will be rejected."
        ]

    return checklist
