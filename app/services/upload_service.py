import uuid
from pathlib import Path
import pymupdf

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload(file: UploadFile) -> dict:
    # 1. Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 2. Read and check size
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()

    if len(content) > MAX_SIZE:  #  > not 
        raise HTTPException(status_code=413, detail="File too large")

    # 3. Sanitize filename
    original_filename = file.filename or "uploaded.pdf"
    safe_name = f"{uuid.uuid4()}_{Path(original_filename).name}"
    file_path = UPLOAD_DIR / safe_name

    with file_path.open("wb") as buffer:
        buffer.write(content)  

    return {
        "filename": file.filename,
        "safe_name": safe_name,
        "file_path": str(file_path),
        "content_type": file.content_type,
        "message": "File uploaded successfully",
    }

def parse_receipt(file_path: str) -> str:     
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        page_text = page.get_text()
        if not isinstance(page_text, str):
            page_text = str(page_text)
        text += page_text
    doc.close()                                 # always close the document
    return text                                 