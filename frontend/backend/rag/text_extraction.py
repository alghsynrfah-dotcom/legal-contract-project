from docx import Document


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


if __name__ == "__main__":
    file_path = "backend/data/contracts/contract.docx"

    extracted_text = extract_text_from_docx(file_path)

    output_file = "backend/rag/extracted_contract.txt"

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(extracted_text)

    print("Text extraction completed successfully.")