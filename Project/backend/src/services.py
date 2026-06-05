import asyncio
import os
from typing import Any
from matplotlib.style import context
from networkx import hits
from .config import EMBEDDING_MODEL

from sqlalchemy.orm import Session

from . import models
from .database import sessionLocal
from .milvus_store import milvus_store

from sentence_transformers import SentenceTransformer

from .llm_service import generate_answer
from .config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from sqlalchemy import text

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


try:
    EMBEDDING_MODEL_INSTANCE = SentenceTransformer(
        EMBEDDING_MODEL,
        local_files_only=True
    )
except Exception:
    EMBEDDING_MODEL_INSTANCE = SentenceTransformer(
        EMBEDDING_MODEL
    )


def _extract_text_from_pdf(file_path: str) -> str:

    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

#currently the chunking is not optimised as it just strip on the basis of character count, we can further improve it by using a more intelligent approach that takes into account sentence boundaries, semantic coherence, or even using a sliding window technique to create overlapping chunks.
def _chunk_text(
    text: str,
) -> list[str]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    return splitter.split_text(text)


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
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return

        doc.status = "processing"
        db.commit()

        text = _extract_text_from_pdf(doc.file_path)
        if not text:
            doc.status = "failed"
            db.commit()
            return

        chunks = _chunk_text(text)
        if not chunks:
            doc.status = "failed"
            db.commit()
            return

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
        print(
            f"DOCUMENT {doc_id} FINISHED"
        )   

    except Exception as exc:  # pragma: no cover - safety path for async task
        db.rollback()
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


async def answer_question(question: str, document_id: int | None = None, top_k: int = 5) -> dict[str, Any]:
    """Retrieve relevant chunks from Milvus and build a grounded response payload."""
    db: Session = sessionLocal()
    try:
        ready_count = db.query(models.Document).filter(models.Document.status == "ready").count()
        if ready_count == 0:
            processing_count = db.query(models.Document).filter(models.Document.status.in_(["uploaded", "processing"])).count()
            if processing_count > 0:
                return {
                    "answer": "Your documents are currently being processed. Please wait a moment and try again.",
                    "citations": []
                }
            return {
                "answer": "No documents are available in the system. Please ingest some PDFs before starting the chat.",
                "citations": []
            }
        
        if document_id is not None:
            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if not doc:
                return {
                    "answer": "The selected document does not exist.",
                    "citations": []
                }
            if doc.status != "ready":
                return {
                    "answer": f"The selected document is not ready yet (current status: {doc.status}).",
                    "citations": []
                }
    finally:
        db.close()

    query_vector = _embed_query(question)
    hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)), document_id=document_id)

    print("\n========== RETRIEVED CHUNKS ==========")

    for idx, hit in enumerate(hits):
        print(
            f"\nChunk {idx+1}"
        )
        safe_content = hit["content"][:300].encode('ascii', errors='replace').decode('ascii')
        print(
            safe_content
        )

    print(
        "\n====================================="
    )

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
    context = "\n\n".join(context_lines)

    answer = await generate_answer(
        question=question,
        context=context,
    )

    return {
        "answer": answer,
        "citations": citations,
    }


async def delete_document_assets(document_id: int, file_path: str | None) -> None:
    """Delete physical file + Milvus vectors for a document."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    milvus_store.delete_document_chunks(document_id)

async def reset_system() -> None:

    print("RESET STARTED")

    db: Session = sessionLocal()

    try:

        print("STEP 1")

        uploads_dir = "uploads"

        if os.path.exists(uploads_dir):
            for file_name in os.listdir(uploads_dir):
                file_path = os.path.join(
                    uploads_dir,
                    file_name,
                )

                if os.path.isfile(file_path):
                    os.remove(file_path)

        print("STEP 2")

        milvus_store.delete_all_chunks()
        print("BEFORE TRUNCATE")

        db.execute(
            text(
                """
                TRUNCATE TABLE
                    document_chunks,
                    documents
                RESTART IDENTITY
                CASCADE
                """
            )
        )

        print("AFTER TRUNCATE")
        db.commit()
        result = db.execute(
            text(
                "SELECT nextval('documents_id_seq')"
            )
        )

        print(
            "NEXTVAL AFTER RESET =",
            result.scalar()
        )
    finally:

        print("STEP 7")

        db.close()
