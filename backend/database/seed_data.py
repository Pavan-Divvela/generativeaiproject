from database.db import get_db_connection, init_db

def seed_database():
    """Seeds the database with comprehensive official document rules and data."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data to avoid duplicates
    cursor.execute("DELETE FROM services")
    cursor.execute("DELETE FROM acceptable_documents")
    cursor.execute("DELETE FROM discrepancy_rules")
    cursor.execute("DELETE FROM faqs")

    # 1. Services
    services_data = [
        # Aadhaar
        (
            'aadhaar_fresh', 'aadhaar', 'Fresh Aadhaar Enrollment',
            'First-time registration for Indian citizens. Requires biometric capture (fingerprints, iris, and facial photo) and demographic verification at an authorized Aadhaar Seva Kendra.',
            'In-Person', 'Free', '15 - 30 days',
            'https://myaadhaar.uidai.gov.in/'
        ),
        (
            'aadhaar_demo_update', 'aadhaar', 'Aadhaar Demographic Update',
            'Update name, address, date of birth, or gender. Address updates can be done online with valid PoA; Name, DoB, and Gender require supporting proofs and visit to an ASK or online portal.',
            'Hybrid', '₹50 (Online Address) / ₹50 (At Kendra)', '5 - 15 days',
            'https://myaadhaar.uidai.gov.in/'
        ),
        (
            'aadhaar_bio_update', 'aadhaar', 'Aadhaar Biometric Update (Ages 5, 15, or Adult)',
            'Mandatory biometric update for children at age 5 and age 15 (Free of cost). Adult biometric re-capture is available for authentication failures.',
            'In-Person', 'Free for minors (5/15 yrs) / ₹100 for adults', '7 - 15 days',
            'https://appointments.uidai.gov.in/easearch.aspx'
        ),
        (
            'aadhaar_pvc_order', 'aadhaar', 'Order Aadhaar PVC Card',
            'Durable pocket-sized PVC card with micro-text, ghost image, and secure QR code delivered by Speed Post.',
            'Online', '₹50 (inclusive of Speed Post)', '7 - 15 working days',
            'https://myaadhaar.uidai.gov.in/gen-pvc'
        ),

        # PAN
        (
            'pan_instant_epan', 'pan', 'Instant e-PAN via Aadhaar e-KYC',
            'Paperless, instant PAN allotment in PDF format for citizens who have a valid Aadhaar linked to an active mobile number and have never been allotted a PAN.',
            'Online', 'Free (Digital PDF) / ₹50 (for physical reprint later)', '10 - 30 minutes',
            'https://eportal.incometax.gov.in/iec/foservices/#/pre-login/instant-e-pan'
        ),
        (
            'pan_new_form49a', 'pan', 'New Physical PAN Card (Form 49A)',
            'Standard application for physical PAN laminated card via Protean (NSDL) or UTIITSL with digital or paper document submission.',
            'Online / Hybrid', '₹107 (Indian address) / ₹1,017 (Foreign address)', '10 - 20 days',
            'https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html'
        ),
        (
            'pan_correction', 'pan', 'PAN Card Correction / Changes',
            'Update name, father name, photo, signature, or address on existing PAN. Essential when PAN details do not match Aadhaar.',
            'Online / Hybrid', '₹107 (Physical) / ₹72 (e-PAN only)', '15 - 25 days',
            'https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html'
        ),
        (
            'pan_aadhaar_link', 'pan', 'PAN-Aadhaar Linking',
            'Mandatory linking for filing Income Tax Returns. Involves paying ₹1,000 penalty via e-Pay Tax before linking if deadline was missed.',
            'Online', '₹1,000 late fee (Minor Head 500)', '2 - 7 days after challan clearance',
            'https://eportal.incometax.gov.in/iec/foservices/#/pre-login/bl-link-aadhaar'
        ),

        # Passport
        (
            'passport_fresh_normal', 'passport', 'Fresh Passport (Normal Scheme)',
            'Standard 36-page or 60-page booklet for fresh applicants. Includes PSK appointment verification and police verification.',
            'Hybrid', '₹1,500 (36 pages) / ₹2,000 (60 pages)', '15 - 30 working days',
            'https://www.passportindia.gov.in/'
        ),
        (
            'passport_fresh_tatkaal', 'passport', 'Fresh Passport (Tatkaal Scheme)',
            'Urgent passport issuance without pre-police verification. Requires 3 specific verification documents or Annexure F verification.',
            'Hybrid', '₹3,500 (36 pages) / ₹4,000 (60 pages)', '3 - 7 working days',
            'https://www.passportindia.gov.in/'
        ),
        (
            'passport_reissue', 'passport', 'Passport Re-issue (Validity Expired / Exhaustion of Pages)',
            'Application for renewal when validity is expiring within 1 year, already expired, pages exhausted, or change in personal particulars.',
            'Hybrid', '₹1,500 (Normal) / ₹3,500 (Tatkaal)', '10 - 25 working days',
            'https://www.passportindia.gov.in/'
        ),
        (
            'passport_pcc', 'passport', 'Police Clearance Certificate (PCC)',
            'Certificate issued to Indian passport holders for immigration, employment, or foreign residency abroad.',
            'Hybrid', '₹500', '7 - 21 working days',
            'https://www.passportindia.gov.in/'
        )
    ]
    cursor.executemany(
        """INSERT INTO services (code, category, title, description, mode, fee, timeline, official_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        services_data
    )

    # 2. Acceptable Documents
    docs_data = [
        # Proof of Identity (PoI)
        ('universal', 'PoI', 'Voter ID Card (EPIC)', 'Election Commission of India', 'Accepted for Aadhaar, PAN, and Passport', 1),
        ('universal', 'PoI', 'Driving Licence', 'Regional Transport Office (RTO)', 'Valid non-expired licence only', 1),
        ('universal', 'PoI', 'Passport', 'Ministry of External Affairs', 'Primary PoI for PAN and Aadhaar', 1),
        ('aadhaar', 'PoI', 'PAN Card / e-PAN', 'Income Tax Department', 'Accepted for Aadhaar updates and enrollment', 1),
        ('aadhaar', 'PoI', 'Ration Card / PDS Card with Photograph', 'State Food Department', 'Must contain applicant photo', 1),
        ('aadhaar', 'PoI', 'Standard Certificate by Gazetted Officer / Tehsildar', 'Govt Gazetted Officer', 'Standard UIDAI Annexure format', 0),
        ('pan', 'PoI', 'Aadhaar Card', 'UIDAI', 'Primary PoI and PoA for PAN applications', 1),
        ('pan', 'PoI', 'Bank Certificate with Photo & Account Number', 'Scheduled Commercial Bank', 'Issued on bank letterhead by Branch Manager', 0),
        ('passport', 'PoI', 'Aadhaar Card / e-Aadhaar', 'UIDAI', 'Mandatory for expedited processing & verification', 1),
        ('passport', 'PoI', 'PAN Card', 'Income Tax Department', 'Secondary identity proof', 1),

        # Proof of Address (PoA)
        ('universal', 'PoA', 'Electricity Bill (not older than 3 months)', 'State Electricity Board', 'In applicant or spouse/parent name', 1),
        ('universal', 'PoA', 'Water Bill (not older than 3 months)', 'Municipal Corporation', 'Must clearly show consumer address', 0),
        ('universal', 'PoA', 'Bank Account Passbook / Statement (last 3 months)', 'Scheduled Commercial Bank', 'Must contain bank stamp, signature, and applicant photo', 1),
        ('universal', 'PoA', 'Registered Rent Agreement', 'Sub-Registrar Office', 'Must be registered; unregistered notary agreements are frequently rejected for Passport', 1),
        ('aadhaar', 'PoA', 'Standard Certificate for Address by MLA / MP / Municipal Councilor', 'Elected Representative', 'On official letterhead with UIDAI Annexure format', 0),
        ('pan', 'PoA', 'Post Office Savings Passbook', 'India Post', 'Current active passbook', 0),
        ('pan', 'PoA', 'Broadband / Landline Telephone Bill', 'Telecom Provider', 'Within 3 months', 0),
        ('passport', 'PoA', 'Aadhaar Card / e-Aadhaar (DigiLocker / Color Print)', 'UIDAI', 'Most accepted proof of present address', 1),
        ('passport', 'PoA', 'Spouses Passport Copy', 'Ministry of External Affairs', 'With endorsement of spouse name', 0),

        # Proof of Date of Birth (PoB)
        ('universal', 'PoB', 'Birth Certificate', 'Registrar of Births & Deaths / Municipal Corporation', 'Highest priority proof across all services', 1),
        ('universal', 'PoB', '10th / Matriculation School Leaving Certificate / Marks Sheet', 'Recognized Education Board (CBSE, ICSE, State)', 'Shows full name, father name, and exact DoB', 1),
        ('pan', 'PoB', 'Aadhaar Card with complete DD/MM/YYYY', 'UIDAI', 'Accepted only if full Date of Birth is printed (not just birth year)', 1),
        ('passport', 'PoB', 'Aadhaar Card', 'UIDAI', 'Must have full DD/MM/YYYY format', 1),
        ('passport', 'PoB', 'PAN Card', 'Income Tax Department', 'Accepted as secondary proof of birth date', 0),

        # Non-ECR Proof (Emigration Check Not Required for Passport)
        ('passport', 'Non-ECR', 'Matriculation / 10th Standard Pass Certificate', 'Recognized Board', 'Most common proof to eliminate ECR stamp', 1),
        ('passport', 'Non-ECR', 'Degree / Higher Education Certificate', 'UGC/AICTE Recognized University', 'Qualifies for Non-ECR status', 1),
        ('passport', 'Non-ECR', 'Income Tax Return (ITR) Proof for last 1 year with Tax Paid', 'Income Tax Dept', 'Applicable for individual taxpayers and their spouses', 1),
        ('passport', 'Non-ECR', 'Senior Citizen Certificate (Age above 50 years)', 'Documentary proof of age', 'Citizens aged 50+ automatically qualify for Non-ECR', 1)
    ]
    cursor.executemany(
        """INSERT INTO acceptable_documents (category, proof_type, document_name, issuer, notes, is_popular)
           VALUES (?, ?, ?, ?, ?, ?)""",
        docs_data
    )

    # 3. Discrepancy Rules
    discrepancy_data = [
        (
            'spelling_minor', 'Aadhaar vs PAN vs Passport', 'Medium',
            'Minor typographical variation (e.g., "Suresh" vs "Sureshkumar", or "Choudhury" vs "Chowdhury").',
            'Update Aadhaar first to match your 10th School Certificate, as Aadhaar is the base document for PAN and Passport.',
            0, 0
        ),
        (
            'initial_expansion', 'PAN vs Aadhaar', 'High',
            'PAN card allows expanded initials only (Income Tax database does not permit single-letter surnames or initials without full name). Aadhaar often contains initials like "K. Ramesh".',
            'First update Aadhaar with full expanded name (e.g., "Kottayam Ramesh") using 10th certificate or passport as proof. Then update PAN.',
            0, 0
        ),
        (
            'marriage_surname', 'Aadhaar vs Passport', 'Medium',
            'Woman changing surname after marriage or adding husband name.',
            'No divorce/marriage certificate is strictly mandatory for passport if applying with joint affidavit (Annexure D). However, updating Aadhaar first with marriage certificate or husband endorsement makes all subsequent updates seamless.',
            1, 0
        ),
        (
            'single_name', 'Passport Application', 'High',
            'Applicant has only one single name on Aadhaar/PAN with no surname (e.g., "Pooja"). International visas and Passport rules strongly require a Given Name and Surname.',
            'In Indian Passports, if you only have one name, it will be placed in the "Surname" field and "Given Name" will be blank. Many foreign embassies (like US/Schengen/UAE) reject visas with blank Given Names. It is recommended to add a family name or father name on Aadhaar first.',
            0, 0
        ),
        (
            'dob_mismatch', 'Aadhaar vs PAN vs 10th Certificate', 'High',
            'Birth date differs by day, month, or year across documents.',
            'Birth Certificate or 10th Board Certificate is the supreme proof. Aadhaar allows DoB change only ONCE in a lifetime. Fix Aadhaar with Board Certificate, then apply for PAN correction via Form 49A.',
            0, 0
        ),
        (
            'major_name_change', 'All Identity Documents', 'High',
            'Complete change of name (e.g., from "Amit Roy" to "Kabir Sen").',
            'Requires publication in the Official Gazette of India, two newspaper advertisements (one English, one local vernacular), and a notarized name-change deed poll/affidavit.',
            1, 1
        )
    ]
    cursor.executemany(
        """INSERT INTO discrepancy_rules (case_type, affected_docs, severity, explanation, recommendation, affidavit_required, gazette_required)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        discrepancy_data
    )

    # 4. FAQs
    faqs_data = [
        (
            'linking',
            'Why is my PAN-Aadhaar linking failing with a demographic mismatch error?',
            'PAN-Aadhaar linking fails when Name, Date of Birth, or Gender differs between UIDAI and Income Tax records. If your name has an expanded initial on PAN but an initial on Aadhaar, or your birth year differs, the automated validation will fail. To fix this, identify which document has the correct details according to your 10th marksheet, update the other document, wait 48-72 hours, and retry the link on the e-filing portal.',
            'pan, aadhaar, linking, mismatch, error'
        ),
        (
            'linking',
            'Do I still need to pay ₹1,000 to link PAN with Aadhaar?',
            'Yes. Under Section 234H of the Income Tax Act, linking after June 30, 2023 requires a non-refundable late fee of ₹1,000 paid under Minor Head 500 (Fee) and Major Head 0021 on the Protean e-Pay Tax portal. After payment clearance (usually 24 to 48 hours), you must re-visit the e-filing portal to finalize the linking request.',
            'pan, aadhaar, fee, penalty, 1000, challan'
        ),
        (
            'passport',
            'What is Non-ECR (Emigration Check Not Required) in Passport and do I qualify?',
            'Non-ECR means you do not need emigration clearance to travel abroad for work in 18 designated ECR countries (including UAE, Saudi Arabia, Qatar, Malaysia). Anyone who has passed the 10th standard (Matriculation) or holds higher educational qualifications, or is an income tax payer, or is above 50 years old qualifies for Non-ECR. You simply need to provide your 10th certificate or degree at the PSK.',
            'passport, non-ecr, ecr, matriculation, qualification'
        ),
        (
            'passport',
            'Can I get a passport in Tatkaal if my name on Aadhaar and 10th certificate does not match?',
            'No. Under Tatkaal scheme, verification is expedited and passport officers strictly verify that your name and date of birth match exactly across 3 mandatory identity proofs (e.g. Aadhaar, PAN, Voter ID). Any discrepancies will cause the officer to downgrade your application to Normal scheme.',
            'passport, tatkaal, mismatch, documents, emergency'
        ),
        (
            'aadhaar',
            'How many times can I change my Name and Date of Birth in Aadhaar?',
            'Under UIDAI rules, an individual can update their Name only TWICE in their lifetime, Date of Birth only ONCE in their lifetime (provided it was not marked as verified previously), and Gender only ONCE. For exceptions beyond this limit, an approval from the UIDAI Regional Office with gazette publication is required.',
            'aadhaar, update-limit, dob, name-change, rules'
        ),
        (
            'aadhaar',
            'Can I use a rent agreement as address proof for Aadhaar and Passport?',
            'For Aadhaar, a registered rent agreement or standard certificate from an MP/MLA is accepted. For Passports, the Passport Office accepts ONLY a Registered Rent Agreement executed under the Indian Registration Act 1908 for the current 1-year duration. Simple 11-month notary stamp rent agreements are routinely rejected at PSK.',
            'aadhaar, passport, rent-agreement, address-proof, psk'
        ),
        (
            'pan',
            'What is the difference between Instant e-PAN and regular PAN?',
            'Instant e-PAN is a digitally signed PDF PAN allotted immediately for free based on Aadhaar e-KYC. It has the same legal validity as a physical PAN card. However, it does not carry your physical signature (it has your Aadhaar photo and a digital QR code). You can order a physical plastic reprint of your e-PAN anytime for ₹50 on the Protean or UTIITSL website.',
            'pan, instant-epan, physical-pan, signature, reprint'
        ),
        (
            'general',
            'In what order should I create or update my identity documents?',
            'The Golden Sequence for Indian citizens is: 1. Birth Certificate / 10th Board Certificate (Anchor proof) -> 2. Aadhaar Card (align with 10th cert) -> 3. PAN Card (align with Aadhaar) -> 4. Passport (applied using Aadhaar, PAN, and 10th cert). Keeping this order eliminates 95% of government application rejections.',
            'sequence, order, road-map, anchor-proof, best-practices'
        )
    ]
    cursor.executemany(
        """INSERT INTO faqs (category, question, answer, tags)
           VALUES (?, ?, ?, ?)""",
        faqs_data
    )

    conn.commit()
    conn.close()
    print("Database successfully seeded with official identity rules and data!")

if __name__ == '__main__':
    seed_database()
