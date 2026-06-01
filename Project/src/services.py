import asyncio
import os
from typing import Any
from .config import EMBEDDING_MODEL

from sqlalchemy.orm import Session

from . import models
from .database import sessionLocal
from .milvus_store import milvus_store
from .websocket_manager import manager
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_INSTANCE = SentenceTransformer(
    EMBEDDING_MODEL
)


def _extract_text_from_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

#currently the chunking is not optimised as it just strip on the basis of character count, we can further improve it by using a more intelligent approach that takes into account sentence boundaries, semantic coherence, or even using a sliding window technique to create overlapping chunks.
def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start = max(0, end - overlap)
    return chunks


def _embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = EMBEDDING_MODEL_INSTANCE.encode(
        texts,
        normalize_embeddings=True
    )

    return [vector.tolist() for vector in vectors]


def _embed_query(text: str) -> list[float]:
    return _embed_texts([text])[0]


async def process_document_task(doc_id: int, filename: str) -> None:
    """Background ingestion pipeline for uploaded PDFs."""
    db: Session = sessionLocal()
    try:
        await manager.broadcast(f"{filename}: Text extraction started...")

        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            await manager.broadcast(f"{filename}: Document not found in DB.")
            return

        doc.status = "processing"
        db.commit()

        text = _extract_text_from_pdf(doc.file_path)
        if not text:
            doc.status = "failed"
            db.commit()
            await manager.broadcast(f"{filename}: No extractable text found.")
            return

        chunks = _chunk_text(text)
        if not chunks:
            doc.status = "failed"
            db.commit()
            await manager.broadcast(f"{filename}: Chunking produced no content.")
            return

        await manager.broadcast(f"{filename}: Generating embeddings...")
        embeddings = _embed_texts(chunks)

        milvus_ids = milvus_store.upsert_chunks(document_id=doc_id, chunks=chunks, embeddings=embeddings)

        db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id == doc_id).delete()
        db.bulk_save_objects(
            [
                models.DocumentChunk(
                    document_id=doc_id,
                    chunk_index=index,
                    content=chunk,
                    milvus_id=str(milvus_ids[index]) if index < len(milvus_ids) else None,
                )
                for index, chunk in enumerate(chunks)
            ]
        )

        doc.status = "ready"
        db.commit()
        await manager.broadcast(f"{filename}: Ready for chat.")

    except Exception as exc:  # pragma: no cover - safety path for async task
        db.rollback()
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
        await manager.broadcast(f"Error processing {filename}: {str(exc)}")
    finally:
        db.close()


async def answer_question(question: str, document_id: int | None = None, top_k: int = 5) -> dict[str, Any]:
    """Retrieve relevant chunks from Milvus and build a grounded response payload."""
    query_vector = _embed_query(question)
    hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)), document_id=document_id)

    if not hits:
        return {
            "answer": "The provided documents do not contain sufficient information to answer this question.",
            "citations": [],
        }

    citations = [
        {
            "document_id": hit["document_id"],
            "chunk_index": hit["chunk_index"],
            "score": hit["score"],
            "content_preview": hit["content"][:220],
        }
        for hit in hits
    ]

    context_lines = [
        f"[Source {idx + 1}] {hit['content']}" for idx, hit in enumerate(hits)
    ]
    answer = "\n\n".join(context_lines)

    return {
        "answer": answer,
        "citations": citations,
    }


def delete_document_assets(document_id: int, file_path: str | None) -> None:
    """Delete physical file + Milvus vectors for a document."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    milvus_store.delete_document_chunks(document_id)
