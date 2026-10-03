"""Hybrid RAG store on plain PostgreSQL.

Rafah (ingestion):
    add_chunks(contract_id, [{"content": ..., "page": ...}, ...])

Shahd (tools/agent):
    retrieve_chunks(contract_id, query, k)

Retrieval combines:
1. Semantic search using embedding cosine similarity.
2. Keyword search using important words from the query.
3. A combined score so exact terms can help semantic retrieval.
"""

import re

import numpy as np
from sqlalchemy import delete, select

from .config import EMBEDDING_DIM
from .db import SessionLocal
from .models import Contract, ContractChunk
from .embeddings import BGEEmbeddings
from .errors import AppError


_emb = BGEEmbeddings()


# Arabic/English words that usually do not help retrieval.
STOP_WORDS = {
    # Arabic
    "ما",
    "ماذا",
    "متى",
    "كيف",
    "هل",
    "من",
    "عن",
    "في",
    "على",
    "إلى",
    "و",
    "أو",
    "هو",
    "هي",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "أي",
    "كم",
    "كان",
    "كانت",
    "يكون",
    "تكون",
    "ماهي",
    "هي",
    # English
    "what",
    "when",
    "where",
    "who",
    "how",
    "is",
    "are",
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "and",
    "or",
}


def _normalize_text(text: str) -> str:
    """Normalize text to make keyword matching more tolerant."""
    text = text.lower()

    # Remove Arabic diacritics.
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

    # Normalize common Arabic letter variants.
    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ى", "ي")

    # Keep Arabic, English and numbers.
    text = re.sub(r"[^\w\s]", " ", text)

    return text.strip()


def _query_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from the user's query."""
    normalized = _normalize_text(query)

    words = normalized.split()

    keywords = [
        word
        for word in words
        if len(word) >= 2 and word not in STOP_WORDS
    ]

    return list(dict.fromkeys(keywords))


def _keyword_score(content: str, keywords: list[str]) -> float:
    """Calculate a simple normalized keyword-match score."""
    if not keywords:
        return 0.0

    normalized_content = _normalize_text(content)

    matched = sum(
        1
        for keyword in keywords
        if keyword in normalized_content
    )

    return matched / len(keywords)


def add_chunks(contract_id: str, chunks: list[dict]) -> int:
    """Embed and store contract chunks."""
    if not chunks:
        raise AppError("NO_CONTENT", "No chunks to store", 422)

    try:
        vectors = _emb.embed_documents(
            [c["content"] for c in chunks]
        )
    except Exception as e:
        raise AppError(
            "RAG_FAILED",
            f"Embedding failed: {e}",
            502,
        )

    if any(len(v) != EMBEDDING_DIM for v in vectors):
        raise AppError(
            "RAG_FAILED",
            f"Embedding size mismatch (expected {EMBEDDING_DIM})",
            502,
        )

    with SessionLocal() as db:
        # Idempotent re-ingest:
        # remove old chunks before inserting the new ones.
        db.execute(
            delete(ContractChunk).where(
                ContractChunk.contract_id == contract_id
            )
        )

        db.add_all(
            ContractChunk(
                contract_id=contract_id,
                chunk_index=i,
                page=c.get("page"),
                content=c["content"],
                embedding=v,
            )
            for i, (c, v) in enumerate(zip(chunks, vectors))
        )

        db.commit()

    return len(chunks)


def retrieve_chunks(
    contract_id: str,
    query: str,
    k: int = 5,
) -> list[dict]:
    """Retrieve chunks using hybrid semantic + keyword search."""

    try:
        # --------------------------------------------------
        # 1. Semantic search
        # --------------------------------------------------
        q = np.asarray(
            _emb.embed_query(query),
            dtype=np.float32,
        )

        with SessionLocal() as db:
            rows = db.execute(
                select(
                    ContractChunk,
                    Contract.name,
                )
                .join(
                    Contract,
                    Contract.contract_id
                    == ContractChunk.contract_id,
                )
                .where(
                    ContractChunk.contract_id == contract_id
                )
            ).all()

        if not rows:
            return []

        matrix = np.asarray(
            [chunk.embedding for chunk, _ in rows],
            dtype=np.float32,
        )

        semantic_scores = (
            matrix @ q
        ) / (
            np.linalg.norm(matrix, axis=1)
            * np.linalg.norm(q)
            + 1e-9
        )

        # --------------------------------------------------
        # 2. Keyword search
        # --------------------------------------------------
        keywords = _query_keywords(query)

        keyword_scores = np.asarray(
            [
                _keyword_score(
                    chunk.content,
                    keywords,
                )
                for chunk, _ in rows
            ],
            dtype=np.float32,
        )

        # --------------------------------------------------
        # 3. Normalize semantic scores
        # --------------------------------------------------
        semantic_min = float(np.min(semantic_scores))
        semantic_max = float(np.max(semantic_scores))

        if semantic_max - semantic_min > 1e-9:
            semantic_normalized = (
                semantic_scores - semantic_min
            ) / (
                semantic_max - semantic_min
            )
        else:
            semantic_normalized = np.zeros_like(
                semantic_scores
            )

        # --------------------------------------------------
        # 4. Hybrid score
        #
        # Semantic gets more weight because it understands
        # meaning, while keyword matching helps exact facts.
        # --------------------------------------------------
        hybrid_scores = (
            0.50 * semantic_normalized
            + 0.50 * keyword_scores
        )

        top = np.argsort(-hybrid_scores)[:k]

    except Exception as e:
        raise AppError(
            "RAG_FAILED",
            f"Retrieval failed: {e}",
            502,
        )

    return [
        {
            "text": rows[i][0].content,
            "source": {
                "contract_name": rows[i][1],
                "page": rows[i][0].page,
                "chunk": rows[i][0].content[:200],
            },
        }
        for i in top
    ]