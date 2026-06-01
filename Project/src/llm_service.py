import google.generativeai as genai
from src.config import GEMINI_API_KEY

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def generate_answer(
    question: str,
    context: str,
) -> str:

    prompt = f"""
You are a document QA assistant.

Rules:
1. Answer ONLY using the provided context.
2. If the answer is not present, say so.
3. Do not invent facts.

Question:
{question}

Context:
{context}
"""

    response = model.generate_content(prompt)

    return response.text