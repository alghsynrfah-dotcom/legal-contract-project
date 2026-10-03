import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def create_embeddings(chunks: list[str]) -> list[list[float]]:
    api_url = os.getenv("EMBEDDING_API_URL")
    api_key = os.getenv("EMBEDDING_API_KEY")
    model = os.getenv("EMBEDDING_MODEL")

    if not api_url:
        raise ValueError("EMBEDDING_API_URL is not set")

    if not api_key:
        raise ValueError("EMBEDDING_API_KEY is not set")

    if not model:
        raise ValueError("EMBEDDING_MODEL is not set")

    client = OpenAI(
        base_url=api_url,
        api_key=api_key
    )

    response = client.embeddings.create(
        model=model,
        input=chunks
    )

    return [item.embedding for item in response.data]


if __name__ == "__main__":
    input_file = "backend/rag/extracted_contract.txt"

    with open(input_file, "r", encoding="utf-8") as file:
        text = file.read()

    from chunking import split_contract_text

    chunks = split_contract_text(text)

    print(f"Total chunks: {len(chunks)}")

    embeddings = create_embeddings(chunks)

    print(f"Total embeddings: {len(embeddings)}")

    if embeddings:
        print(f"Embedding dimension: {len(embeddings[0])}")
        print("First embedding:")
        print(embeddings[0][:10])