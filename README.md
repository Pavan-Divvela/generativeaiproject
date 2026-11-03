# 🇮🇳 Aadhaar, PAN & Passport Process Helper

> **AI-powered guidance assistant** for Indian government identity document procedures — Aadhaar (UIDAI), PAN Card (Income Tax Dept.) and Passport (MEA). Answers are grounded in official government PDFs via a RAG (Retrieval-Augmented Generation) pipeline.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Folder Structure](#folder-structure)
4. [Quick Start](#quick-start)
5. [RAG Setup — Adding Official PDFs](#rag-setup--adding-official-pdfs)
6. [Running the Application](#running-the-application)
7. [API Reference](#api-reference)
8. [Running Tests](#running-tests)
9. [Troubleshooting](#troubleshooting)
10. [Security & Privacy Notes](#security--privacy-notes)
11. [Disclaimer](#disclaimer)

---

## Project Overview

This web application helps Indian citizens understand the step-by-step process for:
- **Aadhaar** — Enrollment, demographic/biometric corrections, PVC card, Masked Aadhaar
- **PAN Card** — Instant e-PAN, Form 49A, PAN-Aadhaar linking, correction requests
- **Passport** — Normal/Tatkaal scheme, Non-ECR status, police verification readiness, document checklists
- **Citizen Account & Login** — Authenticated login, registration, and personalized dashboard to save and track customized document checklists across devices.

### Demo Account Credentials
- **Email:** `demo@example.com`
- **Password:** `Password@123`
*(A 1-click "Auto Fill" button is available on the Login page for testing)*

### How the Chatbot Works

```
User Question
     │
     ▼
[ChromaDB Vector Search]  ←── Official Government PDFs
     │ top-4 relevant chunks
     ▼
[Gemini 2.0 Flash LLM]   ←── System prompt (grounding + anti-hallucination rules)
     │
     ▼
Grounded Answer + Citations (clickable official links)
```

When no PDFs are ingested yet, the chatbot automatically falls back to a keyword-based knowledge engine (still accurate and useful).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML + CSS + JavaScript |
| Backend | Python 3.11+ · Flask 3.1 |
| LLM | Google Gemini 2.0 Flash (via REST API) |
| Vector DB | ChromaDB (persistent local storage) |
| Embeddings | sentence-transformers (local, no API key needed) |
| PDF Parsing | pypdf |
| Database | SQLite (checklist & service metadata) |
| Testing | pytest |

---

## Folder Structure

```
aadhaar-pan-passport-helper/
├── backend/
│   ├── app.py                      # Flask application entry point
│   ├── config.py                   # App-level configuration
│   ├── requirements.txt
│   ├── .env                        # ← YOUR API KEY (gitignored)
│   ├── .env.example                # Safe template (no secrets)
│   │
│   ├── rag/                        # ✨ NEW: RAG pipeline modules
│   │   ├── __init__.py
│   │   ├── config.py               # RAG-specific settings
│   │   ├── schemas.py              # Pydantic request/response models
│   │   ├── pdf_ingest.py           # PDF → chunks → ChromaDB
│   │   ├── retriever.py            # ChromaDB semantic search
│   │   └── generator.py           # Gemini grounded answer generation
│   │
│   ├── routes/
│   │   ├── chatbot.py              # POST /api/chat (updated)
│   │   ├── checklist.py
│   │   └── services.py
│   │
│   ├── services/
│   │   ├── rag_service.py          # Orchestrator (updated)
│   │   ├── llm_service.py          # Gemini API + keyword fallback
│   │   └── guidance_service.py
│   │
│   ├── knowledge_base/             # Existing BM25 fallback
│   │   ├── documents/              # Markdown knowledge files
│   │   └── processed/chunks.json
│   │
│   └── database/                   # SQLite (checklist data)
│
├── frontend/
│   ├── pages/
│   │   ├── index.html
│   │   ├── chatbot.html            # Updated: service selector + citation links
│   │   ├── aadhaar.html
│   │   ├── pan.html
│   │   ├── passport.html
│   │   ├── process-guide.html
│   │   └── faq.html
│   ├── css/ · js/ · assets/
│
├── data/                           # ✨ NEW: RAG data directory
│   ├── raw/
│   │   ├── aadhaar/               # ← Place Aadhaar PDFs here
│   │   ├── pan/                   # ← Place PAN PDFs here
│   │   └── passport/              # ← Place Passport PDFs here
│   ├── chroma_db/                 # Auto-created by ingestion
│   └── source_manifest.json       # Maps PDF filename → official URL
│
└── tests/
    ├── test_rag_ingest.py          # ✨ NEW
    ├── test_rag_retrieval.py       # ✨ NEW
    ├── test_rag_generator.py       # ✨ NEW
    ├── test_services.py
    ├── test_checklist.py
    └── test_chatbot.py
```

---

## Quick Start

### 1. Clone & Setup

```powershell
# Windows PowerShell
cd C:\Users\syamb\.gemini\antigravity\scratch
git clone <your-repo-url> aadhaar-pan-passport-helper
cd aadhaar-pan-passport-helper
```

### 2. Create Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

> ⚠️ `sentence-transformers` downloads PyTorch (~130 MB on first install). This is a one-time download used for local embeddings without any API key.

### 4. Configure Environment

```powershell
# Copy the template
Copy-Item .env.example .env

# Edit .env and add your Gemini API key
notepad .env
```

Set `GEMINI_API_KEY=your_actual_key_here`.

---

## RAG Setup — Adding Official PDFs

> [!IMPORTANT]
> The chatbot works immediately without PDFs (using the keyword fallback engine). PDFs make it significantly more accurate and grounded.

### Step 1: Download Official PDFs

Download PDFs only from verified government portals:

| Service | Source | Download URL |
|---------|--------|-------------|
| Aadhaar | UIDAI | https://uidai.gov.in/en/my-aadhaar/about-your-aadhaar/overview.html |
| PAN | Income Tax Dept | https://www.incometax.gov.in/iec/foportal/help/how-to-apply-for-pan |
| Passport | Passport Seva (MEA) | https://www.passportindia.gov.in/AppOnlineProject/pdf/FormInstructions.pdf |

### Step 2: Place PDFs in the Correct Folders

```
data/raw/aadhaar/   → UIDAI enrollment & update PDFs
data/raw/pan/       → Income Tax / NSDL / CBDT PDFs
data/raw/passport/  → MEA / Passport Seva PDFs
```

### Step 3: Update `data/source_manifest.json`

Add an entry for each PDF with its **verified official URL**:

```json
{
  "aadhaar": {
    "your_file.pdf": {
      "title": "Official Title of the Document",
      "official_url": "https://exact.official.gov.in/url",
      "description": "What this document covers"
    }
  }
}
```

> [!CAUTION]
> Never invent URLs. If you don't have a verified URL, leave `official_url` blank and note it manually. The citation system will not display a link for entries without a URL.

### Step 4: Run Ingestion

```powershell
# From the project root
cd C:\Users\syamb\.gemini\antigravity\scratch\aadhaar-pan-passport-helper
python -m backend.rag.pdf_ingest

# To rebuild from scratch (wipe existing ChromaDB and re-ingest all):
python -m backend.rag.pdf_ingest --rebuild
```

**Expected output:**
```
10:30:00 [INFO] Processing: aadhaar_enrollment_correction.pdf
10:30:02 [INFO]   ✓ aadhaar_enrollment_correction.pdf: 47 chunks upserted (12 pages)
10:30:05 [INFO] Ingestion complete: 3 documents processed, 142 new chunks upserted.
10:30:05 [INFO] ChromaDB collection 'aadhaar_pan_passport' now contains 142 total chunks.
```

---

## Running the Application

```powershell
# From the backend/ directory
cd backend
python app.py
```

Open your browser: **http://127.0.0.1:5000**

The chatbot is at: **http://127.0.0.1:5000/chatbot.html**

---

## API Reference

### `POST /api/chat`

**Request:**
```json
{
  "message": "What documents are required for a Tatkaal passport?",
  "service": "passport"   // optional: "aadhaar" | "pan" | "passport"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "answer": "### Tatkaal Passport Requirements\n\n...",
    "sources": [
      {
        "id": "source-1",
        "title": "Passport Application Instructions",
        "service": "passport",
        "official_url": "https://www.passportindia.gov.in/...",
        "page_range": "p4"
      }
    ],
    "citations": [...],
    "suggestions": ["..."],
    "source_mode": "chroma_rag"   // or "keyword_fallback"
  }
}
```

### `GET /api/chat/suggestions`

Returns starter questions to display in the chat UI.

### `GET /api/health`

Returns server health status.

---

## Running Tests

```powershell
# From project root — run ALL tests
cd C:\Users\syamb\.gemini\antigravity\scratch\aadhaar-pan-passport-helper
python -m pytest tests/ -v

# Run only RAG tests
python -m pytest tests/test_rag_ingest.py tests/test_rag_retrieval.py tests/test_rag_generator.py -v

# Run original tests (should still pass)
python -m pytest tests/test_services.py tests/test_chatbot.py tests/test_checklist.py -v
```

> All RAG tests are fully mocked — no API calls, no credits spent.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'chromadb'"
```powershell
pip install chromadb sentence-transformers pypdf pytest
```

### "GEMINI_API_KEY is not set"
Edit `backend/.env` and set `GEMINI_API_KEY=your_key_here`.

### PDF pages showing as empty
The PDF is likely a scanned image. `pypdf` can only extract text from text-based PDFs. For scanned PDFs, you need OCR. Install `pytesseract` and `pdf2image` and pre-process the PDF before ingestion.

### ChromaDB collection always empty after ingestion
- Check that PDFs are in `data/raw/aadhaar/`, `data/raw/pan/`, or `data/raw/passport/`
- Run with `--rebuild` flag: `python -m backend.rag.pdf_ingest --rebuild`
- Check ingestion logs for warnings about empty pages

### CORS errors in browser console
The Flask app uses `flask-cors`. If you're running frontend on a different port, update the CORS config in `backend/app.py`.

### Gemini API returns 404 for model
Change `GEMINI_MODEL` in `backend/.env` to a supported model. Currently confirmed working: `gemini-2.0-flash`, `gemini-1.5-flash`.

### sentence-transformers download takes very long
The first run downloads the embedding model (~90 MB). Subsequent runs use the cached model. This is a one-time cost.

---

## Security & Privacy Notes

- **API keys are backend-only** — the `GEMINI_API_KEY` is never sent to the browser
- **`.env` is gitignored** — never commit your API key
- **No identity data collected** — the chatbot does not store Aadhaar numbers, PAN numbers, or passport details
- **Informational guidance only** — this app does not submit real applications or access government databases
- **Document text treated as untrusted** — the RAG system prompt instructs the LLM to ignore any instructions embedded in PDF content (prompt injection guard)

---

## Disclaimer

> This application provides **general informational guidance** based on official government documents. It is **not affiliated with UIDAI, Income Tax Department, or Ministry of External Affairs**. For official decisions, always visit the respective government portals or Aadhaar Seva Kendras / Protean centers / Passport Seva Kendras in person.

---

*Built for the ICL Gen AI Mastery program · 2026*
