import shutil
import uuid
from pathlib import Path
import pymupdf

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload(file: UploadFile) -> dict:
    # 1. Validate before touching the filesystem
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read(MAX_SIZE + 1)
    
    if len(content) < MAX_SIZE:
        return HTTPException(413, "File too large")

    # 2. Sanitize filename
    safe_name = f"{uuid.uuid4()}_{Path(file.filename).name}"
    file_path = UPLOAD_DIR / safe_name

    # 3. Save to disk
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "safe_name": safe_name,        # useful later for passing to parser
        "file_path": str(file_path),   # useful later for RAG / LLM pipeline
        "content_type": file.content_type,
        "message": "File uploaded successfully",
    }

def parse_receipt(file_path: str) -> str:     
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()                                 # always close the document
    return text                                 