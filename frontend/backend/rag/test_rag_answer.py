from rag_answer import generate_rag_answer


questions = [
    "ما هي مدة العقد؟",
    "متى يتم تسليم النسخة التشغيلية الأولى؟",
    "ما هي شروط إنهاء العقد؟"
]


if __name__ == "__main__":

    for question in questions:

        print("\n" + "=" * 60)
        print(f"QUESTION: {question}")
        print("=" * 60)

        result = generate_rag_answer(
            question=question,
            contract_id="contract_001",
            top_k=3
        )

        print("\nANSWER:")
        print(result["answer"])

        print("\nSOURCES:")

        for source in result["sources"]:
            print(source)