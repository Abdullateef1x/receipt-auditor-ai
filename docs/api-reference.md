# Receipt Auditor AI
## API Reference

**Base URL:** `http://127.0.0.1:8000`

This reference documents the HTTP endpoints exposed by Receipt Auditor AI. The API accepts PDF uploads for expense policies and receipts, indexes policy content for retrieval, and generates expense audit reports.

## 1. Health and application status

### `GET /health`

Checks whether the application is responding.

**Request**

No parameters required.

**Successful response — `200 OK`**

```json
{
  "status": "ok"
}
```

### `GET /`

Returns a basic application status message.

**Request**

No parameters required.

**Successful response — `200 OK`**

```json
{
  "message": "Receipt Auditor AI running"
}
```

## 2. Policy management

### `POST /policy`

Uploads an expense policy PDF and indexes its extracted text for retrieval during receipt auditing.

**Request**

Content type: `multipart/form-data`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | PDF file | Yes | Expense policy document |

**Successful response — `200 OK`**

```json
{
  "filename": "expense-policy.pdf",
  "chunks_indexed": 12,
  "message": "Policy uploaded and indexed successfully"
}
```

`chunks_indexed` represents the number of text chunks added to the policy index. The value depends on the uploaded document.

**Possible errors**

| Status | Description |
|---|---|
| `400 Bad Request` | The uploaded file is not identified as a PDF |
| `422 Unprocessable Entity` | The PDF could not be parsed or contains no readable text |
| `500 Internal Server Error` | The policy could not be indexed |

### `GET /policy/status`

Checks whether the policy index contains indexed content.

**Request**

No parameters required.

**Successful response — `200 OK`**

When policies are indexed:

```json
{
  "ready": true,
  "chunks_indexed": 12,
  "message": "Policy database is ready"
}
```

When the index is empty:

```json
{
  "ready": false,
  "chunks_indexed": 0,
  "message": "No policies indexed yet"
}
```

### `DELETE /policy/reset`

Removes all indexed policy chunks from the policy collection.

**Request**

No parameters required.

**Successful response — `200 OK`**

```json
{
  "message": "Policy index cleared"
}
```

**Important:** This operation clears the policy index. It should not be treated as a general-purpose deletion of every policy file stored on disk.

## 3. Receipt auditing

### `POST /upload`

Uploads a receipt PDF for extraction, validation, policy comparison, and report generation.

**Request**

Content type: `multipart/form-data`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | PDF file | Yes | Receipt to audit |

**File constraints**

- The uploaded file must be identified as `application/pdf`.
- The maximum accepted receipt size is 10 MiB (10 × 1024 × 1024 bytes).

**Processing overview**

1. The receipt PDF is saved and its text is extracted.
2. An AI service extracts receipt fields.
3. Deterministic validation checks selected monetary values.
4. Relevant policy chunks are retrieved.
5. An AI service evaluates potential policy anomalies.
6. A PDF audit report is generated and uploaded to Cloudflare R2.
7. The report record is stored in the database.

The request waits for the processing pipeline to complete.

**Successful response — `200 OK`**

```json
{
  "report_id": "A1B2C3D4",
  "status": "flagged",
  "anomalies_count": 2,
  "recommendation": "Review the flagged items before approval.",
  "confidence": 0.91,
  "report_url": "https://example.com/presigned-report-url",
  "created_at": "2026-11-23T20:30:00"
}
```

The values above are illustrative. The `report_url` returned by the API is a temporary, presigned download URL.

**Possible errors**

| Status | Description |
|---|---|
| `400 Bad Request` | The uploaded file is not identified as a PDF |
| `413 Payload Too Large` | The receipt exceeds the size limit |
| `422 Unprocessable Entity` | The PDF could not be parsed |
| `500 Internal Server Error` | Extraction, validation, anomaly analysis, report generation, or another processing step failed |

## 4. Audit reports

### `GET /reports`

Returns stored audit reports, ordered by creation time from newest to oldest.

**Request**

No query parameters are currently implemented.

**Successful response — `200 OK`**

```json
{
  "total": 1,
  "reports": [
    {
      "report_id": "A1B2C3D4",
      "filename": "receipt.pdf",
      "vendor": "Example Vendor",
      "total_amount": 12500.0,
      "status": "flagged",
      "confidence": 0.91,
      "created_at": "2026-11-23T20:30:00",
      "pdf_url": "https://example.com/presigned-report-url"
    }
  ]
}
```

The example values are illustrative.

Each report's `pdf_url` is generated as a temporary presigned URL. The current implementation sets the URL expiration to one hour.

## 5. General behaviour and limitations

- The API does not currently expose authentication or authorization.
- The API does not currently provide pagination or filtering for `GET /reports`.
- Receipt and policy PDFs are processed as text-based documents. The current PDF extraction implementation does not perform OCR.
- Policy indexing uses a local ChromaDB persistence directory.
- Audit report records are stored in the configured PostgreSQL database.
- Generated report PDFs are stored in Cloudflare R2.
- The API's anomaly status is an automated assessment, not a final approval decision. Final approval remains the responsibility of the designated approver.