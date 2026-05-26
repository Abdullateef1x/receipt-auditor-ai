import chromadb
from chromadb.utils import embedding_functions

chroma_client = chromadb.PersistentClient(path="./policy_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="company_policies",
    embedding_function=embedding_fn # type: ignore[arg-type]

)


def chunking(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def retrieve_relevant_policies(query: str, n_results: int = 3) -> list[str]:
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents"]
    )
    if not results or not results.get("documents"):
        return []
    
    documents = results["documents"]
    if documents is None or len(documents) == 0:
        return []
    
    return documents[0] or []