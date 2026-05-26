# 🧾 Receipt Auditor AI — LLM-Powered Financial Compliance System

An AI-powered financial auditing backend that automatically processes expense receipts, extracts structured financial data, compares transactions against company policies using RAG, and generates PDF compliance audit reports with anomaly detection and LLM reasoning.

Designed as a **production-style LLM system with vector search, document intelligence, and structured output pipelines.**

---

## ⚡ What This System Does

Receipt Auditor AI automates financial compliance end-to-end:

- 📄 Upload receipt (PDF)
- 🔍 Extract text using document parsing (PyMuPDF)
- 🧠 Structure data using LLM extraction (Groq LLaMA 3.3 70B)
- 📚 Retrieve relevant company policy chunks (ChromaDB RAG)
- 🚨 Detect anomalies and policy violations (LLM reasoning)
- 📊 Generate a structured PDF audit report (ReportLab)
- 📦 Upload report to Cloudflare R2, save metadata to Supabase
- 📥 Return report URL + audit insights

---

## 🧠 System Architecture

```
PDF Receipt Upload
        ↓
PyMuPDF Text Extraction
        ↓
LLM Structured Extraction (Groq LLaMA 3.3 70B)
        ↓
Embedding + Vector Search (ChromaDB + Sentence Transformers)
        ↓
Policy Retrieval (RAG Layer)
        ↓
LLM Anomaly Detection + Compliance Reasoning
        ↓
PDF Audit Report Generation (ReportLab)
        ↓
Cloud Storage (Cloudflare R2 + Supabase)
        ↓
JSON API Response (Report URL + Audit Insights)
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| LLM Engine | Groq (LLaMA 3.3 70B) |
| RAG System | ChromaDB + Sentence Transformers |
| Document Parsing | PyMuPDF |
| Report Generation | ReportLab |
| File Storage | Cloudflare R2 |
| Database | Supabase (PostgreSQL) + SQLModel |
| Containerization | Docker |
| Deployment | Railway |
| Dependency Management | Poetry |

---

## 🏗️ Project Structure

```
receipt-auditor-ai/
├── app/
│   ├── main.py                    # App entry point, route registration, CORS
│   ├── api/
│   │   └── routes/
│   │       ├── upload.py          # /upload, /reports endpoints
│   │       └── policy.py          # /policy, /policy/status, /policy/reset
│   ├── core/
│   │   └── rag.py                 # ChromaDB, embeddings, chunking, retrieval
│   ├── db/
│   │   └── database.py            # SQLModel engine + session
│   ├── models/
│   │   └── report.py              # AuditReport SQLModel table
│   └── services/
│       ├── ai_service.py          # Groq LLM extraction + anomaly analysis
│       ├── upload_service.py      # Receipt upload, validation, sanitization
│       ├── policy_service.py      # Policy upload + PDF parsing
│       ├── report_service.py      # ReportLab PDF audit report generation
│       └── storage_service.py     # Cloudflare R2 upload
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── poetry.lock
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Poetry
- [Groq](https://console.groq.com) API key
- [Supabase](https://supabase.com) project
- [Cloudflare R2](https://cloudflare.com) bucket

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/receipt-auditor-ai.git
cd receipt-auditor-ai
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in your `.env`:

```bash
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_BUCKET_NAME=receipt-auditor
R2_PUBLIC_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com/receipt-auditor
```

### 4. Run locally

```bash
poetry run uvicorn app.main:app --reload
```

### 5. Run with Docker

```bash
docker compose up --build
```

---

## 📡 API Endpoints

### `POST /policy`
Upload a company expense policy PDF to index into ChromaDB.

```bash
curl -X POST http://localhost:8000/policy \
  -F "file=@company_expense_policy.pdf"
```

**Response:**
```json
{
  "filename": "company_expense_policy.pdf",
  "chunks_indexed": 42,
  "message": "Policy uploaded and indexed successfully"
}
```

---

### `GET /policy/status`
Check how many policy chunks are indexed and ready for retrieval.

```bash
curl http://localhost:8000/policy/status
```

---

### `DELETE /policy/reset`
Clear all indexed policy chunks from ChromaDB.

```bash
curl -X DELETE http://localhost:8000/policy/reset
```

---

### `POST /upload`
Upload a receipt PDF. Runs the full AI pipeline and returns audit results + report URL.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@receipt.pdf"
```

**Response:**
```json
{
  "report_id": "A1B2C3D4",
  "status": "flagged",
  "anomalies_count": 3,
  "recommendation": "Verify pre-approval for expense and review line items",
  "confidence": 0.85,
  "report_url": "https://your-bucket.r2.cloudflarestorage.com/reports/audit_A1B2C3D4_receipt.pdf",
  "created_at": "2025-05-14T20:42:00"
}
```

---

### `GET /reports`
List all previously generated audit reports with metadata.

```bash
curl http://localhost:8000/reports
```

---

### `GET /health`
Health check.

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 🧪 Testing the Full Pipeline

> **Important:** Always upload a policy before uploading a receipt.

```bash
# Step 1 — Index a policy
curl -X POST http://localhost:8000/policy \
  -F "file=@company_expense_policy.pdf"

# Step 2 — Confirm it's indexed
curl http://localhost:8000/policy/status

# Step 3 — Upload a receipt
curl -X POST http://localhost:8000/upload \
  -F "file=@receipt.pdf"
```

---

## 📊 Audit Report

Each generated PDF report contains:

| Section | Details |
|---|---|
| Status Banner | Approved / Flagged / Rejected with color coding |
| Invoice Details | Vendor, date, invoice number, payment method, tax, total |
| Line Items | Full itemized breakdown |
| Anomaly Analysis | Per-field violations with Low / Medium / High severity |
| Recommendation | AI-generated compliance recommendation |
| Confidence Score | Model confidence in the audit findings |

Reports are stored in Cloudflare R2 and metadata is persisted in Supabase.

---

## 🧠 Skills Demonstrated

- LLM orchestration (Groq / LLaMA 3.3 70B)
- Retrieval-Augmented Generation (RAG)
- Vector databases (ChromaDB)
- Structured LLM outputs with Pydantic validation
- FastAPI backend engineering
- Document intelligence pipelines (PyMuPDF)
- Cloud storage integration (Cloudflare R2)
- Relational database persistence (Supabase + SQLModel)
- Containerization (Docker)
- Production deployment (Railway)

---

## 🌍 Why This Project Matters

Demonstrates end-to-end AI system design skills relevant to:

- AI Engineer roles
- LLM Application Engineer positions
- Backend Engineer (AI Systems)
- AI Full-Stack Engineer positions

---

## 📄 License

MIT