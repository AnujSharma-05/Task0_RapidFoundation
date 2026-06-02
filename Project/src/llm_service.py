import asyncio

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

    response = await model.generate_content(prompt)

    return response.text