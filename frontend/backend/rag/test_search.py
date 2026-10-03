from embedding import create_embeddings
from vector_store import search_contract


CONTRACT_ID = "contract_001"


def test_search(question: str):
    # تحويل السؤال إلى embedding
    query_embedding = create_embeddings([question])[0]

    # البحث داخل Vector DB
    results = search_contract(
        query_embedding=query_embedding,
        contract_id=CONTRACT_ID,
        top_k=3
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print("\n========== SEARCH RESULTS ==========")

    for index, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1
    ):
        print(f"\n--- Result {index} ---")
        print(f"Distance: {distance}")
        print(f"Metadata: {metadata}")
        print("Content:")
        print(document)


if __name__ == "__main__":
    question = "120000 دولار"

    print(f"Question: {question}")

    test_search(question)