import os

from dotenv import load_dotenv
from openai import OpenAI

from rag_service import retrieve_hybrid_chunks


load_dotenv()


def generate_rag_answer(
    question: str,
    contract_id: str,
    top_k: int = 3
) -> dict:
    """
    Retrieve relevant contract chunks and generate
    an answer using the LLM.
    """

    # 1. Retrieve relevant chunks
    retrieved_chunks = retrieve_hybrid_chunks(
    question=question,
    contract_id=contract_id,
    top_k=top_k
)

    if not retrieved_chunks:
        return {
            "answer": "لم يتم العثور على معلومات مرتبطة بالسؤال داخل العقد.",
            "sources": []
        }

    # 2. Build context from retrieved chunks
    context_parts = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"[المصدر {index}]\n"
            f"{chunk['content']}"
        )

    context = "\n\n".join(context_parts)

    # 3. Read LLM configuration
    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model = os.getenv("MODEL_NAME")

    if not api_url:
        raise ValueError("VLLM_API_URL is not set")

    if not api_key:
        raise ValueError("VLLM_API_KEY is not set")

    if not model:
        raise ValueError("MODEL_NAME is not set")

    # 4. Create LLM client
    client = OpenAI(
        base_url=api_url,
        api_key=api_key
    )

    # 5. Ask the LLM to answer using only retrieved context
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "أنت مساعد قانوني يجيب عن الأسئلة المتعلقة بالعقود. "
                    "استخدم المعلومات الموجودة في السياق فقط. "
                    "لا تخترع أي معلومات غير موجودة في السياق. "
                    "إذا لم تجد الإجابة في السياق، قل بوضوح إن المعلومات "
                    "غير موجودة في الأجزاء المسترجعة من العقد."
                )
            },
            {
                "role": "user",
                "content": (
                    f"السؤال:\n{question}\n\n"
                    f"السياق المسترجع من العقد:\n{context}\n\n"
                    "أجب عن السؤال بشكل واضح ومختصر."
                )
            }
        ]
    )

    answer = response.choices[0].message.content

    # 6. Prepare source information
    sources = []

    for chunk in retrieved_chunks:
        sources.append(
            {
                "filename": chunk["metadata"].get("filename"),
                "chunk_index": chunk["metadata"].get("chunk_index"),
                "distance": chunk["distance"]
            }
        )

    return {
        "answer": answer,
        "sources": sources
    }