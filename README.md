# 🧾 Receipt Auditor AI — AI-Powered Financial Compliance Backend

Receipt Auditor AI is an AI-powered financial auditing backend that processes expense receipts, extracts structured financial data, evaluates transactions against company expense policies, and generates PDF audit reports with anomaly detection.

It combines document processing, LLM-based extraction, Retrieval-Augmented Generation (RAG), and deterministic financial validation in an end-to-end FastAPI application.

## ⚡ What This System Does

The application automates an expense auditing workflow:

- 📄 Accepts PDF receipt uploads.
- 🔍 Extracts receipt text using PyMuPDF.
- 🧠 Extracts structured financial information using Groq (LLaMA 3.3 70B).
- 📚 Retrieves relevant expense policy sections using ChromaDB and Sentence Transformers.
- 🚨 Analyzes potential anomalies and policy compliance using an LLM.
- 🧮 Validates financial amounts using deterministic validation logic.
- 📊 Generates PDF audit reports using ReportLab.
- 📦 Stores generated reports in Cloudflare R2.
- 🗄️ Persists report metadata in Supabase PostgreSQL.
- 📥 Generates temporary download URLs for stored reports.

## 🧠 System Architecture

```text
PDF Receipt Upload
        ↓
PyMuPDF Text Extraction
        ↓
LLM Structured Extraction (Groq)
        ↓
Financial Validation
        ↓
Embedding + Vector Search
(ChromaDB + Sentence Transformers)
        ↓
Relevant Policy Retrieval (RAG)
        ↓
LLM Anomaly Analysis
        ↓
PDF Audit Report Generation
(ReportLab)
        ↓
Cloud Storage (Cloudflare R2)
        ↓
Metadata Persistence
(Supabase PostgreSQL)
        ↓
JSON API Response
(Audit Results + Download URL)
```

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| LLM | Groq (LLaMA 3.3 70B) |
| RAG | ChromaDB + Sentence Transformers |
| Document Parsing | PyMuPDF |
| Financial Validation | Python |
| Report Generation | ReportLab |
| Object Storage | Cloudflare R2 |
| Database | Supabase PostgreSQL + SQLModel |
| Containerization | Docker |
| Deployment | Render |
| Dependency Management | Poetry |

## 🏗️ Project Structure

```text
receipt-auditor-ai/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       ├── upload.py
│   │       └── policy.py
│   ├── core/
│   │   └── rag.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   └── report.py
│   └── services/
│       ├── ai_service.py
│       ├── upload_service.py
│       ├── validation_service.py
│       ├── policy_service.py
│       ├── report_service.py
│       └── storage_service.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── poetry.lock
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Poetry
- Groq API key
- Supabase project with PostgreSQL
- Cloudflare R2 bucket

### 1. Clone the repository

```bash
git clone https://github.com/Abdullateef1x/receipt-auditor-ai.git
cd receipt-auditor-ai
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```env
GROQ_API_KEY=your_groq_api_key

DATABASE_URL=your_supabase_postgresql_connection_string

R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=receipt-auditor
```

Keep your `.env` file private. Never commit API keys, database credentials, or storage secrets to Git.

### 4. Run locally

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 5. Run with Docker

```bash
docker compose up --build
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/policy` | Upload and index an expense policy PDF |
| GET | `/policy/status` | Check indexed policy information |
| DELETE | `/policy/reset` | Clear indexed policy chunks |
| POST | `/upload` | Upload and audit a receipt |
| GET | `/reports` | Retrieve previously generated reports |
| GET | `/health` | Check API health |

### Upload an expense policy

```bash
curl -X POST http://localhost:8000/policy \
  -F "file=@company_expense_policy.pdf"
```

### Check policy indexing status

```bash
curl http://localhost:8000/policy/status
```

### Upload a receipt

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@receipt.pdf"
```

The upload endpoint processes the receipt and returns audit information, including the report ID, audit status, anomaly count, recommendation, confidence score, and a temporary report download URL.

Example response:

```json
{
  "report_id": "A1B2C3D4",
  "status": "flagged",
  "anomalies_count": 3,
  "recommendation": "Verify expense documentation and approval evidence.",
  "confidence": 0.85,
  "report_url": "<temporary-presigned-download-url>",
  "created_at": "2026-11-18T10:30:00"
}
```

### Retrieve previous reports

```bash
curl http://localhost:8000/reports
```

The reports endpoint returns stored report metadata and freshly generated download URLs.

## 📦 Report Storage

Generated PDF reports are stored privately in Cloudflare R2.

Instead of storing expiring download URLs in the database, the application stores the report's R2 object key.

When a report is requested:

1. The API retrieves the stored object key.
2. The storage service generates a new presigned download URL.
3. The API returns the URL to the client.

Download URLs expire after **one hour**.

This approach avoids relying on expired URLs stored in database records. The storage service also supports legacy records containing previously stored full URLs.

## 🧪 Testing the Full Pipeline

Upload an expense policy before testing receipt auditing.

**Step 1 — Index an expense policy**

```bash
curl -X POST http://localhost:8000/policy \
  -F "file=@company_expense_policy.pdf"
```

**Step 2 — Verify policy indexing**

```bash
curl http://localhost:8000/policy/status
```

**Step 3 — Upload a receipt**

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@receipt.pdf"
```

**Step 4 — Retrieve generated reports**

```bash
curl http://localhost:8000/reports
```

## 📊 Audit Report Contents

Each generated PDF report includes:

| Section | Description |
|---|---|
| Status | Audit outcome |
| Invoice Details | Vendor, date, invoice number, payment method, tax, and total |
| Line Items | Extracted itemized expenses |
| Anomaly Analysis | Identified discrepancies and potential policy issues |
| Recommendation | Suggested follow-up actions |
| Confidence Score | LLM-reported confidence score |

## 🧠 Skills Demonstrated

- Backend engineering with FastAPI
- LLM integration and structured data extraction
- Retrieval-Augmented Generation (RAG)
- Vector search and semantic retrieval
- Pydantic-based data validation
- Financial validation and anomaly detection
- PDF document processing
- Cloud object storage integration
- Relational database persistence
- Docker-based application setup
- API design and error handling

## 🌍 Project Relevance

Receipt Auditor AI demonstrates practical engineering work across:

- AI/LLM application development
- Backend engineering
- Document intelligence
- Financial automation
- Retrieval-Augmented Generation systems

## Technical Documentation

Explore the technical documentation and engineering articles for this project:

**[View Technical Writing Portfolio](docs/README.md)**

Includes the API Quickstart, API Reference, Render Deployment Tutorial, and Architecture Deep Dive.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.