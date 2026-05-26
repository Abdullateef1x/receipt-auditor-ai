from sentence_transformers import SentenceTransformer
import chromadb

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./policy_db")
collection = chroma_client.get_or_create_collection(name="company_policies")


def chunking(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def retrieve_relevant_policies(query: str, n_results: int = 3) -> list[str]:
    query_embedding = embedding_model.encode([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents"]
    )
    if (
        not results
        or not results.get("documents")
        or results.get("documents") is None
        or not results["documents"]
        or results["documents"][0] is None
    ):
        return []
    return results["documents"][0]