# ── Stage 1: Builder ─────────────────────────────────────────
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

# ✅ Install CPU-only torch FIRST before poetry install
# This prevents poetry from pulling 2GB+ CUDA/nvidia packages
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# ✅ Download model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

COPY ./app ./app

RUN mkdir -p uploaded_files policy_files audit_reports policy_db

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]