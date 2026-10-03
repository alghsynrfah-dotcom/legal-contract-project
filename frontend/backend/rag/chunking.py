from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_contract_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            "،",
            " ",
            ""
        ]
    )

    return splitter.split_text(text)


if __name__ == "__main__":
    input_file = "backend/rag/extracted_contract.txt"

    with open(input_file, "r", encoding="utf-8") as file:
        text = file.read()

    chunks = split_contract_text(text)

    print(f"Total chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print(f"\n========== CHUNK {index} ==========")
        print(chunk)