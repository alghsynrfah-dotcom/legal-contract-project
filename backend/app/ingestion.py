
from pathlib import Path

from shared.db import SessionLocal
from shared.models import Contract
from shared.storage import get_file_path
from shared import rag_store
from shared.errors import AppError


# --------------------------------------------------
# Text extraction
# --------------------------------------------------

def extract_text(file_path: Path, file_type: str) -> list[dict]:
    """
    Extract text from the uploaded contract.

    Returns:
        [
            {
                "content": "...",
                "page": 1
            },
            ...
        ]
    """

    if file_type == "txt":
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        if not text.strip():
            raise AppError(
                "NO_CONTENT",
                "The contract contains no readable text",
                422,
            )

        return [
            {
                "content": text,
                "page": None,
            }
        ]

    if file_type == "docx":
        try:
            from docx import Document
        except ImportError:
            raise AppError(
                "DEPENDENCY_MISSING",
                "python-docx is required to read DOCX files",
                500,
            )

        document = Document(str(file_path))

        paragraphs = [
            p.text.strip()
            for p in document.paragraphs
            if p.text.strip()
        ]

        if not paragraphs:
            raise AppError(
                "NO_CONTENT",
                "The DOCX file contains no readable text",
                422,
            )

        return [
            {
                "content": "\n".join(paragraphs),
                "page": None,
            }
        ]

    if file_type == "pdf":
        try:
            import fitz
        except ImportError:
            raise AppError(
                "DEPENDENCY_MISSING",
                "PyMuPDF is required to read PDF files",
                500,
            )

        document = fitz.open(str(file_path))

        pages = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "content": text,
                        "page": page_number,
                    }
                )

        document.close()

        if not pages:
            raise AppError(
                "NO_CONTENT",
                "The PDF contains no readable text",
                422,
            )

        return pages

    raise AppError(
        "UNSUPPORTED_FILE_TYPE",
        f"Unsupported file type: {file_type}",
        422,
    )


# --------------------------------------------------
# Chunking
# --------------------------------------------------

def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks.

    This keeps the ingestion independent from the frontend
    and stores chunks in the shared RAG store.
    """

    text = text.strip()

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# --------------------------------------------------
# Build RAG chunks
# --------------------------------------------------

def build_chunks(pages: list[dict]) -> list[dict]:
    """
    Convert extracted pages into chunks while preserving
    the original page number.
    """

    chunks = []

    for page in pages:
        page_chunks = split_text(page["content"])

        for chunk in page_chunks:
            chunks.append(
                {
                    "content": chunk,
                    "page": page.get("page"),
                }
            )

    if not chunks:
        raise AppError(
            "NO_CONTENT",
            "No usable chunks were created from the contract",
            422,
        )

    return chunks


# --------------------------------------------------
# Update ingestion status
# --------------------------------------------------

def set_ingestion_status(contract_id: str, status: str) -> None:
    with SessionLocal() as db:
        contract = db.get(Contract, contract_id)

        if not contract:
            raise AppError(
                "CONTRACT_NOT_FOUND",
                f"Contract '{contract_id}' not found",
                404,
            )

        contract.ingestion_status = status
        db.commit()


# --------------------------------------------------
# Main ingestion pipeline
# --------------------------------------------------

def ingest_contract(contract_id: str) -> None:
    """
    Full contract ingestion pipeline:

        Storage
           ↓
        Text Extraction
           ↓
        Chunking
           ↓
        Embedding
           ↓
        Shared RAG Store
           ↓
        ready
    """

    try:
        # 1. Get contract metadata from DB
        with SessionLocal() as db:
            contract = db.get(Contract, contract_id)

            if not contract:
                raise AppError(
                    "CONTRACT_NOT_FOUND",
                    f"Contract '{contract_id}' not found",
                    404,
                )

            file_path_key = contract.file_path
            file_type = contract.file_type

        # 2. Mark as processing
        set_ingestion_status(
            contract_id,
            "processing",
        )

        # 3. Get physical file from shared storage
        file_path = get_file_path(file_path_key)

        # 4. Extract text
        pages = extract_text(
            file_path,
            file_type,
        )

        # 5. Chunk extracted text
        chunks = build_chunks(pages)

        # 6. Store chunks + generate embeddings
        rag_store.add_chunks(
            contract_id,
            chunks,
        )

        # 7. Mark ingestion as ready
        set_ingestion_status(
            contract_id,
            "ready",
        )

        # 8. Let Shahd's post-ingestion logic extract
        # contract dates / information if available.
        try:
            from .tools import post_ingestion

            post_ingestion(contract_id)

        except Exception:
            # The main ingestion succeeded.
            # Post-ingestion extraction should not make
            # the contract appear as failed.
            pass

    except Exception:
        try:
            set_ingestion_status(
                contract_id,
                "failed",
            )
        except Exception:
            pass

        # BackgroundTasks will log the exception.
        raise
