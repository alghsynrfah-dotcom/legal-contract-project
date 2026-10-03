from rag_service import keyword_search


if __name__ == "__main__":
    question = "ما هي قيمة العقد؟"

    results = keyword_search(
        question=question,
        contract_id="contract_001",
        top_k=3
    )

    print("\n========== KEYWORD SEARCH RESULTS ==========")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Keyword Score: {result['keyword_score']}")
        print(f"Metadata: {result['metadata']}")
        print("Content:")
        print(result["content"])