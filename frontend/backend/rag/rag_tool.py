from rag_answer import generate_rag_answer


def search_contract_tool(
    question: str,
    contract_id: str
) -> dict:
    """
    Search a contract using hybrid RAG
    and return the answer with sources.
    """

    result = generate_rag_answer(
        question=question,
        contract_id=contract_id,
        top_k=3
    )

    return result


if __name__ == "__main__":
    question = "ما هي قيمة العقد؟"
    contract_id = "contract_001"

    result = search_contract_tool(
        question=question,
        contract_id=contract_id
    )

    print("\n========== RAG TOOL TEST ==========")

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")

    for source in result["sources"]:
        print(source)