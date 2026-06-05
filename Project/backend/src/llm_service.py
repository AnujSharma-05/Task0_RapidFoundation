import asyncio
from typing import Any

import google.generativeai as genai
from src.config import GEMINI_API_KEY

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


async def generate_answer(
    question: str,
    context: str,
) -> str:

    prompt = f"""
        You are a RAG-based document assistant.

        You MUST follow these rules:

        1. Answer ONLY from the provided context.
        2. Do NOT invent information.
        3. If the answer is not found in the context, say:
        "The provided document does not contain enough information to answer this question."
        4. Keep answers concise and factual.
        5. Use bullet points when appropriate.

        QUESTION:
        {question}

        CONTEXT:
        {context}
    """

    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
    )

    return response.text


async def classify_ingested_document(text_sample: str, existing_categories: list[str]) -> str:
    """Classify an uploaded document into an existing category or create a new specific category."""
    categories_str = ", ".join(f"'{c}'" for c in existing_categories) if existing_categories else "None"
    
    prompt = f"""
        You are an intelligent document classification system.
        Your job is to analyze the text sample of a new document and assign it to the most relevant category.

        Active categories in the database: [{categories_str}]

        Rules:
        1. If the document fits one of the existing categories, respond with that category name exactly.
        2. If the document does not fit any existing category, propose a new, specific, and concise category name (e.g., "Lord of the Rings", "Deep Learning", "Company Policies"). Do not create redundant or overly broad categories (like "PDF", "Document", "Book").
        3. Respond ONLY with the category name string (no quotes, no preamble, no markdown formatting).

        TEXT SAMPLE FROM DOCUMENT:
        {text_sample[:3000]}
    """
    
    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
    )
    
    return response.text.strip().replace("'", "").replace('"', "")


async def classify_query_category(question: str, category_candidates: list[dict[str, Any]]) -> str:
    """Classify the user's query into the most suitable category from the candidate list."""
    candidates_str = "\n".join(
        f"- Category: '{c['category_name']}'\n  Summary: {c['summary']}"
        for c in category_candidates
    )
    
    prompt = f"""
        You are a search query router.
        Your job is to map a user question to the most relevant document category based on the summaries of candidate categories.

        CANDIDATE CATEGORIES AND SUMMARIES:
        {candidates_str}

        Rules:
        1. Respond with the exact name of the most matching category.
        2. Respond ONLY with the category name (no quotes, no preamble, no explanation).

        USER QUESTION:
        {question}
    """
    
    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
    )
    
    return response.text.strip().replace("'", "").replace('"', "")