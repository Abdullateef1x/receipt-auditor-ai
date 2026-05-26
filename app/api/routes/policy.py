from app.core.rag import chunking, collection, embedding_model
from app.services.policy_service import parse_policy, save_policy
from fastapi import APIRouter, File, HTTPException, UploadFile
from pathlib import Path

router = APIRouter(prefix="/policy", tags=["Policy"])


@router.post("")
async def upload_policy(file: UploadFile = File(...)):
    saved = await save_policy(file)
    file_path = saved["file_path"]

    try:
        text = parse_policy(file_path)
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not parse policy PDF: {e}")

    if not text.strip():
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Policy PDF appears empty or unreadable")

    try:
        policy_id = saved["safe_name"]
        chunks = chunking(text)
        embeddings = embedding_model.encode(chunks).tolist()
        collection.add(
            ids=[f"{policy_id}_chunk_{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=embeddings
        )
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to index policy: {e}")

    return {
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "message": "Policy uploaded and indexed successfully",
    }


@router.get("/status")
def policy_status():
    count = collection.count()
    return {
        "chunks_indexed": count,
        "ready": count > 0,
        "message": "Policy database is ready" if count > 0 else "No policies indexed yet"
    }


@router.delete("/reset")
def reset_policies():
    existing = collection.get()
    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
    return {"message": "Policy index cleared"}