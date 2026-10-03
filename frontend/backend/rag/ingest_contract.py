from chunking import split_contract_text
from embedding import create_embeddings
from vector_store import store_contract_chunks, collection


INPUT_FILE = "backend/rag/extracted_contract.txt"

CONTRACT_ID = "contract_001"
FILENAME = "contract.docx"


def ingest_contract():
    # 1. قراءة النص المستخرج
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        text = file.read()

    print("Text loaded successfully.")

    # 2. تقسيم النص إلى chunks
    chunks = split_contract_text(text)

    print(f"Total chunks: {len(chunks)}")

    # 3. إنشاء embeddings
    embeddings = create_embeddings(chunks)

    print(f"Total embeddings: {len(embeddings)}")

    # 4. تخزين chunks + embeddings داخل ChromaDB
    store_contract_chunks(
        chunks=chunks,
        embeddings=embeddings,
        contract_id=CONTRACT_ID,
        filename=FILENAME
    )

    print("Contract stored successfully in ChromaDB.")
    print(f"Total stored chunks: {collection.count()}")


if __name__ == "__main__":
    ingest_contract()