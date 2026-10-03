from rag_service import retrieve_hybrid_chunks


if __name__ == "__main__":
    question = "ما هي قيمة العقد؟"

    results = retrieve_hybrid_chunks(
        question=question,
        contract_id="contract_001",
        top_k=3
    )

    print("\n========== HYBRID SEARCH RESULTS ==========")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Hybrid Score: {result['hybrid_score']}")
        print(f"Keyword Score: {result['keyword_score']}")
        print(f"Semantic Score: {result['semantic_score']}")
        print(f"Distance: {result['distance']}")
        print(f"Metadata: {result['metadata']}")
        print("Content:")
        print(result["content"])