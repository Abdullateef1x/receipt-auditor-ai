import shutil
import uuid
from pathlib import Path

import pymupdf
from fastapi import HTTPException, UploadFile

POLICY_DIR = Path("policy_files")
POLICY_DIR.mkdir(exist_ok=True)


async def save_policy(file: UploadFile) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # ✅ file.filename can be None — provide a fallback
    original_filename = file.filename or "uploaded.pdf"
    safe_name = f"{uuid.uuid4()}_{Path(original_filename).name}"
    file_path = POLICY_DIR / safe_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "safe_name": safe_name,
        "file_path": str(file_path),
    }


def parse_policy(file_path: str) -> str:
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        # ✅ get_text() returns str | list | dict — cast explicitly to str
        text += str(page.get_text())
    doc.close()
    return text