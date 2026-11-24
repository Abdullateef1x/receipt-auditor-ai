# Receipt Auditor AI — Quickstart

Receipt Auditor AI is an API that extracts structured information from receipt PDFs, checks financial amounts, evaluates expenses against indexed company policies, and generates downloadable PDF audit reports.

This guide explains how to configure and run the application locally.

## Prerequisites

Before getting started, ensure you have:

- Python 3.12 or later
- Poetry
- A Supabase PostgreSQL database
- A Groq API key
- A Cloudflare R2 bucket and access credentials

## 1. Clone the repository

```bash
git clone https://github.com/Abdullateef1x/receipt-auditor-ai.git
cd receipt-auditor-ai
```

## 2. Install dependencies

Install the project dependencies using Poetry:

```bash
poetry install
```

## 3. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key

DATABASE_URL=your_supabase_postgresql_connection_url

R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=receipt-auditor
```

Replace the placeholder values with your actual credentials.

The application uses:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates AI requests through Groq |
| `DATABASE_URL` | Connects to the PostgreSQL database |
| `R2_ACCOUNT_ID` | Identifies the Cloudflare account |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret key |
| `R2_BUCKET_NAME` | Name of the R2 bucket used for generated reports |

The application loads environment variables using `python-dotenv`.

## 4. Start the application

Run the FastAPI application with Uvicorn:

```bash
poetry run uvicorn app.main:app --reload
```

By default, Uvicorn serves the application at:

```text
http://127.0.0.1:8000
```

The application creates its database tables during startup.

## 5. Check application health

Send a GET request to:

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

You can also access the root endpoint:

```http
GET /
```

Expected response:

```json
{
  "message": "Receipt Auditor AI running"
}
```

## 6. Upload a company expense policy

Before auditing receipts, upload a company policy PDF so its contents can be indexed for retrieval.

**Request**

```http
POST /policy
Content-Type: multipart/form-data
```

The request must contain a file field named `file`.

Example using cURL:

```bash
curl -X POST http://127.0.0.1:8000/policy \
  -F "file=@expense-policy.pdf"
```

Example successful response:

```json
{
  "filename": "expense-policy.pdf",
  "chunks_indexed": 12,
  "message": "Policy uploaded and indexed successfully"
}
```

The exact number of indexed chunks depends on the extracted policy text.

The application extracts text from the PDF, splits it into overlapping chunks, generates embeddings using ChromaDB's default embedding function, and stores the chunks in its persistent local collection.

## 7. Check policy index status

Send:

```http
GET /policy/status
```

Example response:

```json
{
  "chunks_indexed": 12,
  "ready": true,
  "message": "Policy database is ready"
}
```

A `ready` value of `true` indicates that the collection contains indexed chunks.

## 8. Upload a receipt for auditing

Send a PDF receipt to:

```http
POST /upload
Content-Type: multipart/form-data
```

Example using cURL:

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@receipt.pdf"
```

The application processes the receipt by:

1. Extracting text from the PDF.
2. Extracting structured invoice data using an AI model through Groq.
3. Checking financial totals using deterministic validation.
4. Retrieving relevant company policy chunks from ChromaDB.
5. Evaluating the receipt against the retrieved policy context.
6. Generating a PDF audit report.
7. Uploading the report to Cloudflare R2.
8. Saving report metadata in PostgreSQL.

Example successful response:

```json
{
  "report_id": "A1B2C3D4",
  "status": "flagged",
  "anomalies_count": 1,
  "recommendation": "Verify the reported expense amount.",
  "confidence": 0.92,
  "report_url": "https://example-presigned-download-url",
  "created_at": "2026-11-23T12:00:00"
}
```

The values above are illustrative. Actual results depend on the receipt and policy content.

The `report_url` is a temporary Cloudflare R2 presigned download URL that expires after one hour.

## 9. Retrieve generated reports

To list stored audit reports:

```http
GET /reports
```

Example:

```bash
curl http://127.0.0.1:8000/reports
```

The endpoint returns stored report metadata, ordered from newest to oldest, with a newly generated download URL for each report.

## Important notes

- Receipt and policy uploads accept files whose declared content type is `application/pdf`.
- Receipt uploads are limited to 10 MiB.
- Policy uploads do not currently have an explicit file-size limit.
- PDF text extraction uses PyMuPDF. OCR for image-only scanned receipts is not implemented in the reviewed code.
- Policy chunks are stored locally in `./policy_db`, while report metadata is stored in PostgreSQL and generated PDFs are stored in Cloudflare R2.
- The API currently does not implement authentication or user-specific report access.
- The current CORS configuration allows all origins, methods and headers. Review this before production deployment.
- Audit results are automated assessments. Final expense approval remains the responsibility of the designated company approver.