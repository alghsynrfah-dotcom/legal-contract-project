import chromadb


# إنشاء Vector Database محلية
client = chromadb.PersistentClient(
    path="backend/rag/chroma_db"
)


# إنشاء أو الحصول على Collection للعقود
collection = client.get_or_create_collection(
    name="contracts"
)


def store_contract_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    contract_id: str,
    filename: str
):
    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks must match number of embeddings"
        )

    ids = [
        f"{contract_id}_chunk_{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "contract_id": contract_id,
            "filename": filename,
            "chunk_index": index
        }
        for index in range(len(chunks))
    ]

    collection.upsert(
    ids=ids,
    embeddings=embeddings,
    documents=chunks,
    metadatas=metadatas
)


def search_contract(
    query_embedding: list[float],
    contract_id: str,
    top_k: int = 3
):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "contract_id": contract_id
        }
    )

    return results