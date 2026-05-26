from app.api.routes import policy, upload
from app.db.database import create_db_and_tables
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI(title="Receipt Auditor AI")

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten this after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(policy.router)
app.include_router(upload.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"message": "Receipt Auditor AI running"}


@app.get("/health")
def health():
    return {"status": "ok"}