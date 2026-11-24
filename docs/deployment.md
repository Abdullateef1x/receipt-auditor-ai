# Deploying a Dockerized FastAPI Application to Render

*A practical deployment walkthrough using Receipt Auditor AI, Docker, Supabase PostgreSQL, and Cloudflare R2.*

## 1. Introduction

Deploying a FastAPI application involves more than making its endpoints accessible over the internet. The application also needs a reliable configuration, a suitable runtime environment, and access to the services it depends on.

In this tutorial, we'll walk through the deployment architecture of Receipt Auditor AI, a FastAPI application that extracts information from receipt PDFs, validates financial data, compares expenses against company policies, and generates audit reports.

The application uses:

- **FastAPI** for the API layer.
- **Docker** to package the application and its dependencies.
- **Render** to host the application.
- **Supabase PostgreSQL** to store audit records.
- **ChromaDB** to index expense policy documents.
- **Cloudflare R2** to store generated audit reports.
- **Groq** to power AI-based extraction and anomaly analysis.

By the end, you'll understand how to package a FastAPI application with Docker, configure its production environment, deploy it to Render, and verify that its external dependencies are working.

## 2. Prerequisites

Before starting, you'll need:

- Python 3.12 or later.
- Git.
- Docker and Docker Compose.
- A Render account.
- A Supabase PostgreSQL database.
- A Cloudflare R2 bucket.
- A Groq API key.
- A GitHub repository containing your application.

You should also be familiar with basic Python development, environment variables, and REST APIs.

## 3. Run the application locally

Before deploying, verify that the application works in your local environment.

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Install dependencies using Poetry:

```bash
poetry install
```

Create a `.env` file using the example configuration:

```bash
cp .env.example .env
```

Configure the required environment variables:

```env
GROQ_API_KEY=your_groq_api_key

DATABASE_URL=your_supabase_database_url

R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=receipt-auditor
```

Keep credentials out of your source code and never commit your `.env` file.

Start the development server:

```bash
poetry run uvicorn app.main:app --reload
```

By default, Uvicorn makes the application available at:

```text
http://127.0.0.1:8000
```

Verify that the application is running:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

You can also access the automatically generated Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## 4. Package the application with Docker

Docker provides a consistent environment for running the application across development and deployment environments.

Receipt Auditor AI uses a multi-stage Docker build.

### Understanding the builder stage

The first stage installs system dependencies, Poetry, and the application's Python dependencies.

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root
```

Copying the dependency manifests before the application source code allows Docker to cache the dependency installation layer when application code changes without changing dependencies.

### Understanding the runtime stage

The second stage starts from a fresh Python image.

```dockerfile
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./app ./app

RUN mkdir -p uploaded_files policy_files audit_reports policy_db

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Several decisions are important here:

**Separate build and runtime environments:** The final image doesn't need the Poetry installation or compiler tools used during dependency installation.

**Non-root execution:** The container runs as `appuser`, reducing the privileges available to the application process.

**Application directories:** The required directories are created before the application starts.

**Network binding:** Uvicorn listens on `0.0.0.0`, allowing requests to reach the application from outside the container.

**Production startup:** The container starts Uvicorn without the development-only `--reload` option.

## 5. Understand the application configuration

The application relies on environment variables to connect to external services.

The `.env` file is useful during local development, but production credentials should be configured through the hosting platform.

The required variables are:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates requests to Groq |
| `DATABASE_URL` | Connects to Supabase PostgreSQL |
| `R2_ACCOUNT_ID` | Identifies the Cloudflare R2 account |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret key |
| `R2_BUCKET_NAME` | Target R2 bucket |

The deployed application uses Supabase PostgreSQL through its connection pooler.

The database URL should be copied from your Supabase project rather than constructed manually.

## 6. Deploy to Render

Render supports Docker-based web services, allowing an application to be deployed from a repository containing a Dockerfile.

### Step 1: Push the application to GitHub

Make sure your latest application code and Dockerfile are committed and pushed to your repository.

Do not include your `.env` file or credentials.

### Step 2: Create a Web Service

1. Sign in to Render.
2. Select **New** and choose **Web Service**.
3. Connect your GitHub account if necessary.
4. Select the repository containing Receipt Auditor AI.
5. Configure the service.

### Step 3: Configure the Docker build

Select Docker as the runtime/build environment where applicable.

Set the Dockerfile path to:

```text
./Dockerfile
```

This tells Render where to find the instructions for building the application image.

The Dockerfile's `CMD` instruction defines the production startup command.

### Step 4: Configure environment variables

Open the service's **Environment** settings.

Add the required variables:

```text
GROQ_API_KEY
DATABASE_URL
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
```

Use the actual credentials from your respective service dashboards.

Do not paste secrets into source files, public documentation, or GitHub commits.

### Step 5: Deploy

Create the Web Service and start the deployment.

Render builds the Docker image and starts the application using the configured container startup command.

Check the deployment logs for build errors, missing environment variables, and application startup failures.

## 7. Verify the deployed application

A successful deployment should be tested rather than assumed from the dashboard's deployment status.

### Check application health

Open the deployed application's public URL followed by:

```text
/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Check policy indexing

Open:

```text
/policy/status
```

The endpoint reports whether the ChromaDB collection contains indexed policy chunks.

For example, after successfully uploading a policy:

```json
{
  "chunks_indexed": 10,
  "ready": true,
  "message": "Policy database is ready"
}
```

### Upload a policy

Use the Swagger UI or an HTTP client to send a PDF to:

```text
POST /policy
```

The endpoint should extract the document text, split it into chunks, and add those chunks to the ChromaDB collection.

### Verify policy retrieval status

Call:

```text
GET /policy/status
```

The indexed chunk count should reflect the uploaded document.

In my deployment, uploading `globaltech_expense_policy_sample.pdf` successfully indexed 10 chunks. A subsequent status request returned `ready: true` and `chunks_indexed: 10`.

This verified that the deployed application could write to and read from its policy index during the running instance.

## 8. Understand storage in production

One important deployment consideration is that not all application data should be stored inside the container filesystem.

Receipt Auditor AI uses different storage systems for different responsibilities.

| Data | Storage location |
|---|---|
| Audit records | Supabase PostgreSQL |
| Generated report PDFs | Cloudflare R2 |
| Policy index | Local ChromaDB directory |
| Uploaded receipt PDFs | Container filesystem |
| Uploaded policy PDFs | Container filesystem |

### The ephemeral filesystem limitation

The deployed Render service does not have a persistent disk attached.

This means files written to the container filesystem are not guaranteed to survive a restart, redeployment, or instance replacement.

This matters particularly for ChromaDB because the application uses a local persistent directory:

```text
./policy_db
```

The word *persistent* in ChromaDB's local configuration refers to its storage behaviour on disk. It does not guarantee that the hosting platform preserves that disk across container replacements.

For a production application that needs policies to remain indexed, consider attaching a persistent disk at the appropriate mount path or moving the index to an external persistent storage solution.

Cloudflare R2 and Supabase provide separate storage for generated reports and audit records, respectively. They do not automatically preserve the local ChromaDB index.

## 9. Troubleshooting

### Application fails to start

Check the Render deployment logs.

Common causes include:

- Missing environment variables.
- Dependency installation failures.
- Incorrect Dockerfile paths.
- Database connection errors.

### Database connection fails

Verify that:

- `DATABASE_URL` is configured correctly.
- The Supabase database is available.
- The connection string uses the intended connection pooler configuration.
- The required database credentials are valid.

### Policy index is empty

Check:

```text
GET /policy/status
```

If the index is empty, upload the policy document again.

If the application was restarted or redeployed, investigate whether the local ChromaDB directory was preserved.

### Report generation fails

Check the application logs and verify that:

- The R2 account ID is correct.
- The access key and secret are valid.
- The bucket exists.
- The application has permission to upload objects.

## 10. Conclusion

Deploying a FastAPI application involves more than packaging code into a Docker image. The application must also be configured correctly, connected to its external services, and tested in its production environment.

Receipt Auditor AI demonstrates how Docker, Render, Supabase PostgreSQL, ChromaDB, and Cloudflare R2 can work together in a single application.

It also highlights an important production consideration: a container's filesystem should not be assumed to provide durable storage.

Understanding where application data lives, how it is accessed, and what happens when a container is replaced is essential when designing reliable deployments.