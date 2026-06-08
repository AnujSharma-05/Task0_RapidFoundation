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


async def update_categorical_summary(category_name: str) -> None:
    """Consolidate document contents in the category and update its Milvus summary embedding."""
    if not category_name or category_name == "general":
        return

    db: Session = sessionLocal()
    try:
        # Fetch all documents in this category
        docs = db.query(models.Document).filter(
            models.Document.category == category_name,
            models.Document.status == "ready"
        ).all()
        
        if not docs:
            return

        # Compile summaries or first chunks of documents to create a category context
        context_parts = []
        for doc in docs:
            # Get first chunk content
            first_chunk = db.query(models.DocumentChunk).filter(
                models.DocumentChunk.document_id == doc.id
            ).order_by(models.DocumentChunk.chunk_index.asc()).first()
            
            if first_chunk:
                context_parts.append(f"Document '{doc.filename}': {first_chunk.content[:1000]}")

        category_context = "\n\n".join(context_parts)
        
        # Call LLM to generate summary
        prompt = f"""
            Generate a concise, unified 2-3 sentence summary describing the scope and topic of this category of documents.
            Category Name: {category_name}
            Documents Context:
            {category_context}
        """
        
        from .llm_service import model
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
        )
        summary_text = response.text.strip()
        
        # Generate summary embedding
        summary_vector = _embed_query(summary_text)
        
        # Upsert in Milvus
        milvus_store.upsert_category_summary(
            category_name=category_name,
            summary=summary_text,
            embedding=summary_vector
        )
        print(f"Updated category summary for '{category_name}': {summary_text[:100]}...")

    except Exception as exc:
        print("Failed to update categorical summary:", exc)
    finally:
        db.close()


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

        # --- Dynamic Automated Categorization ---
        resolved_category = doc.category
        if not resolved_category or resolved_category == "general":
            # 1. Try vector-based matching against existing summaries
            first_chunk_vector = _embed_query(chunks[0])
            try:
                matches = milvus_store.search_categories(first_chunk_vector, top_k=1)
                if matches and matches[0]["score"] >= 0.60:
                    resolved_category = matches[0]["category_name"]
                    print(f"Vector-matched category: {resolved_category} (score: {matches[0]['score']})")
            except Exception as e:
                print("Milvus category search skipped/failed:", e)

            # 2. Fallback to LLM Classification
            if not resolved_category or resolved_category == "general":
                try:
                    # Get unique category names from PostgreSQL
                    categories_objs = db.query(models.Document.category).distinct().all()
                    existing_categories = [c[0] for c in categories_objs if c[0] and c[0] != "general"]
                    
                    # Call Gemini
                    from . import llm_service
                    resolved_category = await llm_service.classify_ingested_document(
                        text_sample=text[:4000],
                        existing_categories=existing_categories
                    )
                    print(f"LLM-classified category: {resolved_category}")
                except Exception as e:
                    print("LLM classification failed, fallback to general:", e)
                    resolved_category = "general"

            doc.category = resolved_category
            db.commit()

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

        # Trigger summary update in the background
        if resolved_category and resolved_category != "general":
            asyncio.create_task(update_categorical_summary(resolved_category))

    except Exception as exc:  # pragma: no cover - safety path for async task
        db.rollback()
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


async def answer_question(question: str, document_id: int | None = None, category: str | None = None, top_k: int = 5) -> dict[str, Any]:
    """Retrieve relevant chunks from Milvus and build a grounded response payload using hierarchical clustering."""
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
        
        query_vector = _embed_query(question)
        hits = []

        # 1. Bypass check - Specific Document ID Filter
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
            hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)), document_id=document_id)

        # 2. Bypass check - Specific Category Filter
        elif category is not None:
            doc_ids_query = db.query(models.Document.id).filter(
                models.Document.category == category,
                models.Document.status == "ready"
            ).all()
            doc_ids = [r[0] for r in doc_ids_query]
            if doc_ids:
                hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)), document_ids=doc_ids)
            else:
                hits = []

        # 3. Two-Stage Routing Flow (No active manual filter)
        else:
            # Stage 1: Categorical Triage
            try:
                matches = milvus_store.search_categories(query_vector, top_k=5)
            except Exception as exc:
                print("Milvus search_categories failed:", exc)
                matches = []

            # Confidence-Score Fallback (or if no category summaries exist)
            if not matches or matches[0]["score"] < 0.35:
                print(f"Bypassing categorical routing (Top score: {matches[0]['score'] if matches else 'None'} < 0.35). Global search initiated.")
                hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)))
            else:
                # LLM Routing (LLM Call 1)
                from . import llm_service
                try:
                    chosen_category = await llm_service.classify_query_category(
                        question=question,
                        category_candidates=matches
                    )
                    print(f"LLM 1 classified query to category: '{chosen_category}' (Matches were: {[m['category_name'] for m in matches]})")
                except Exception as exc:
                    print("LLM query classification failed, falling back to top matched category:", exc)
                    chosen_category = matches[0]["category_name"]

                # Ensure chosen category exists in candidates, fallback if not
                candidate_names = [m["category_name"] for m in matches]
                if chosen_category not in candidate_names:
                    print(f"Chosen category '{chosen_category}' not in candidate list. Falling back to top match: '{matches[0]['category_name']}'")
                    chosen_category = matches[0]["category_name"]

                # Stage 2: Main Search (Relational Filter)
                doc_ids_query = db.query(models.Document.id).filter(
                    models.Document.category == chosen_category,
                    models.Document.status == "ready"
                ).all()
                doc_ids = [r[0] for r in doc_ids_query]
                if doc_ids:
                    hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)), document_ids=doc_ids)
                else:
                    # In case documents in chosen category are not found/ready, fallback to global
                    print(f"No documents ready in category '{chosen_category}'. Bypassing category filter.")
                    hits = milvus_store.search(query_embedding=query_vector, top_k=max(1, min(top_k, 10)))

    finally:
        db.close()

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
