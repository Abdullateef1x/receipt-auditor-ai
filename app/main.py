# an AI-powered financial compliance backend that parses receipts, retrieves company policy context via RAG, performs anomaly analysis using LLM reasoning, and generates structured audit reports.

from app.schemas.schema import InvoiceData
from app.services.ai_service import ai_extraction, analyze_anomalies
from app.services.upload_service import parse_receipt, save_upload
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile,  HTTPException

from groq import Groq
from pathlib import Path
from pydantic import BaseModel
import shutil
import chromadb
from sentence_transformers import SentenceTransformer



load_dotenv()
app = FastAPI()
client = Groq()

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./policy_db")
collection = chroma_client.get_or_create_collection(name="Company_policies")



UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


def chunking(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def store_policy(policy_text: str, policy_id: str):
    chunks = chunking(policy_text)
    embedding = model.encode([policy_text])[0].tolist()
    collection.add(
        ids=[policy_id],
        documents=[chunks],
        embeddings=[embedding]
    )

def retrieve_relevant_policies(query: str, n_results: int = 3):
    query_embedding = model.encode([query])[0].tolist()
    search_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents"]
    )

    return search_results["documents"][0]


@app.get("/")
def root():
    return {"message": "Receipt Auditor running"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    saved = await save_upload(file)
    file_path = saved["file_path"]

    try:
      text = parse_receipt(file_path)
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {e}")
    
    try:
        extracted_data = ai_extraction(text)
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"AI extraction failed: {e}")
    
    try:
        context = retrieve_relevant_policies(
            f"expense policy for {extracted_data.get('vendor_name', 'unknown vendor')}"
        )
        audit_result = analyze_anomalies(extracted_data, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy retrieval failed: {e}")
    

    return {
       **saved,
       "extracted data": extracted_data,
       "context": context,
       "audit result": audit_result
    }


