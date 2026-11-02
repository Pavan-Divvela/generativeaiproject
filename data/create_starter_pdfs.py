"""
Utility script to generate starter official guidelines PDFs for Aadhaar, PAN, and Passport.
Generates valid standard PDF 1.4 documents without requiring third-party PDF design libraries.
"""
from pathlib import Path

def create_simple_pdf(path: Path, title: str, paragraphs: list[str]):
    stream_lines = ['BT', '/F1 12 Tf', '14 TL', '50 720 Td']
    stream_lines.append(f'({title}) Tj')
    stream_lines.append('T*')
    stream_lines.append('T*')
    for p in paragraphs:
        clean_p = p.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        words = clean_p.split()
        line = ''
        for w in words:
            if len(line) + len(w) + 1 > 75:
                stream_lines.append(f'({line}) Tj')
                stream_lines.append('T*')
                line = w
            else:
                line = f'{line} {w}'.strip()
        if line:
            stream_lines.append(f'({line}) Tj')
            stream_lines.append('T*')
        stream_lines.append('T*')
    stream_lines.append('ET')
    stream_content = '\n'.join(stream_lines).encode('latin1', 'replace')

    body = bytearray()
    body.extend(b'%PDF-1.4\n')

    offsets = []

    def add_obj(obj_bytes):
        offsets.append(len(body))
        body.extend(obj_bytes)
        body.extend(b'\n')

    add_obj(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj')
    add_obj(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj')
    add_obj(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj')

    stream_obj = f'4 0 obj\n<< /Length {len(stream_content)} >>\nstream\n'.encode('latin1') + stream_content + b'\nendstream\nendobj'
    add_obj(stream_obj)

    add_obj(b'5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj')

    xref_offset = len(body)
    body.extend(f'xref\n0 6\n0000000000 65535 f \n'.encode('latin1'))
    for off in offsets:
        body.extend(f'{off:010d} 00000 n \n'.encode('latin1'))

    body.extend(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n'.encode('latin1'))

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(body)
    print(f"Created: {path}")

def generate_all():
    base = Path(__file__).resolve().parent / "raw"

    # 1. Aadhaar
    aadhaar_file = base / "aadhaar" / "aadhaar_enrollment_correction.pdf"
    create_simple_pdf(
        aadhaar_file,
        "UIDAI Aadhaar Enrolment and Update Standard Operating Procedures",
        [
            "Unique Identification Authority of India (UIDAI) issues Aadhaar, a 12-digit unique identity number.",
            "Enrolment for Aadhaar is completely free of charge at all authorized Aadhaar Seva Kendras.",
            "Demographic updates include name, address, date of birth, gender, mobile number and email ID.",
            "Name change is permitted only two times in a lifetime. Valid proof of identity like passport, PAN card, or marksheet is required.",
            "Date of birth update is allowed only once in a lifetime with valid birth certificate or matriculation marksheet.",
            "Mandatory biometric update for children is required at age 5 and age 15, and is completely free of cost.",
            "Demographic update fee is 50 rupees and biometric update fee is 100 rupees at official centers."
        ]
    )

    # 2. PAN
    pan_file = base / "pan" / "pan_application_form49a.pdf"
    create_simple_pdf(
        pan_file,
        "Income Tax Department - PAN Application and Linking Rules",
        [
            "Permanent Account Number (PAN) is a ten-digit alphanumeric identifier issued by the Income Tax Department.",
            "Indian citizens apply through Form 49A via Protean (NSDL) or UTIITSL portals for a fee of 107 rupees.",
            "Instant e-PAN is issued completely free of charge on the Income Tax e-Filing portal using Aadhaar e-KYC.",
            "Under Section 139AA and Section 234H, linking PAN with Aadhaar is mandatory for all taxpayers.",
            "A late fee penalty of 1000 rupees must be paid under Minor Head 500 (Other Receipts) before submitting the link request.",
            "Allow 24 to 48 hours for the payment challan to clear in the tax portal before completing the Aadhaar verification.",
            "Names, date of birth and gender on PAN must match the Aadhaar record exactly. Full expanded names are required."
        ]
    )

    # 3. Passport
    passport_file = base / "passport" / "passport_application_instructions.pdf"
    create_simple_pdf(
        passport_file,
        "Ministry of External Affairs - Passport Seva Guidelines",
        [
            "Passport applications are processed online through the official portal passportindia.gov.in.",
            "Normal scheme passport fee is 1500 rupees for a 36-page booklet with a 10-year validity for adults.",
            "Tatkaal scheme fee is 3500 rupees for 36 pages. Under Tatkaal, passports are dispatched within 1 to 3 working days.",
            "Tatkaal applicants must submit three mandatory identity documents with 100 percent matching personal details.",
            "Non-ECR (Emigration Check Not Required) status is granted to matriculation (10th standard) pass applicants and taxpayers.",
            "Police verification requires physical presence at your current residence along with two neighbor references."
        ]
    )

if __name__ == "__main__":
    generate_all()
