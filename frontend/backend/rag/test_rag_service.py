from rag_service import retrieve_relevant_chunks


if __name__ == "__main__":
    question = "120000 دولار"

    results = retrieve_relevant_chunks(
        question=question,
        contract_id="contract_001",
        top_k=3
    )

    print("\n========== RAG RESULTS ==========")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Distance: {result['distance']}")
        print(f"Metadata: {result['metadata']}")
        print("Content:")
        print(result["content"])