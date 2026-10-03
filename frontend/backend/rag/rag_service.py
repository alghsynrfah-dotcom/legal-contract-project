from embedding import create_embeddings
from vector_store import search_contract, collection


def retrieve_relevant_chunks(
    question: str,
    contract_id: str,
    top_k: int = 3
) -> list[dict]:
    """
    Semantic search only.
    """

    query_embedding = create_embeddings([question])[0]

    results = search_contract(
        query_embedding=query_embedding,
        contract_id=contract_id,
        top_k=top_k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved_chunks = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved_chunks.append(
            {
                "content": document,
                "metadata": metadata,
                "distance": distance
            }
        )

    return retrieved_chunks


def keyword_search(
    question: str,
    contract_id: str,
    top_k: int = 3
) -> list[dict]:
    """
    Simple keyword-based search over stored contract chunks.
    """

    results = collection.get(
        where={
            "contract_id": contract_id
        }
    )

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    question_words = set(
        question
        .replace("؟", "")
        .replace("?", "")
        .split()
    )

    scored_results = []

    for document, metadata in zip(documents, metadatas):
        score = sum(
            1
            for word in question_words
            if len(word) > 2 and word in document
        )

        if score > 0:
            scored_results.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "distance": None,
                    "keyword_score": score
                }
            )

    scored_results.sort(
        key=lambda item: item["keyword_score"],
        reverse=True
    )

    return scored_results[:top_k]


def normalize_arabic(text: str) -> str:
    """
    Normalize common Arabic letter variations.
    """

    return (
        text
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
    )


def retrieve_hybrid_chunks(
    question: str,
    contract_id: str,
    top_k: int = 3
) -> list[dict]:
    """
    Hybrid retrieval:
    combines semantic search with keyword search.
    """

    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    # -----------------------------------------
    # 1. Create embedding for the question
    # -----------------------------------------

    query_embedding = create_embeddings([question])[0]

    # -----------------------------------------
    # 2. Get semantic results for all chunks
    # -----------------------------------------

    semantic_results = search_contract(
        query_embedding=query_embedding,
        contract_id=contract_id,
        top_k=total_chunks
    )

    documents = semantic_results.get("documents", [[]])[0]
    metadatas = semantic_results.get("metadatas", [[]])[0]
    distances = semantic_results.get("distances", [[]])[0]

    # -----------------------------------------
    # 3. Prepare question keywords
    # -----------------------------------------

    normalized_question = normalize_arabic(question)

    question_words = set(
        normalized_question
        .replace("؟", "")
        .replace("?", "")
        .split()
    )

    stop_words = {
        "ما",
        "هي",
        "هو",
        "هل",
        "من",
        "في",
        "عن",
        "على",
        "الى",
        "إلى",
        "هذا",
        "هذه",
        "ذلك",
        "تلك",
        "كم",
        "ماذا",
        "مع",
        "و",
        "او",
        "أو"
    }

    question_words = [
        word
        for word in question_words
        if len(word) > 2 and word not in stop_words
    ]

    # -----------------------------------------
    # 4. Calculate hybrid score
    # -----------------------------------------

    hybrid_results = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        normalized_document = normalize_arabic(document)

        keyword_score = sum(
            normalized_document.count(word)
            for word in question_words
        )

        # Convert distance into a similarity-like score.
        semantic_score = 1 / (1 + distance)

        # Give keyword matching stronger weight
        # because the current embedding model is English-focused.
        hybrid_score = (
            keyword_score * 2
            + semantic_score
        )

        hybrid_results.append(
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
                "keyword_score": keyword_score,
                "semantic_score": semantic_score,
                "hybrid_score": hybrid_score
            }
        )

    # -----------------------------------------
    # 5. Sort by hybrid score
    # -----------------------------------------

    hybrid_results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True
    )

    return hybrid_results[:top_k]