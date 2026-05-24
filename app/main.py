# an AI-powered financial compliance backend that parses receipts, retrieves company policy context via RAG, performs anomaly analysis using LLM reasoning, and generates structured audit reports.

from app.schemas.schema import InvoiceData
from app.services.ai_service import ai_extraction
from app.services.upload_service import parse_receipt, save_upload
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile,  HTTPException

from groq import Groq
from pathlib import Path
from pydantic import BaseModel
import uuid
import shutil


load_dotenv()
app = FastAPI()
client = Groq()

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)





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

    return {
       **saved,
       "extracted data": extracted_data
    }

