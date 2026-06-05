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

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
        )
        return response.text
    except Exception as exc:
        err_msg = str(exc)
        if "429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower() or "exhausted" in err_msg.lower():
            # Graceful Mock fallback utilizing the retrieved context chunks directly
            lines = [line.strip() for line in context.split("\n") if line.strip()]
            clean_lines = []
            for line in lines:
                if line.startswith("[Source"):
                    clean_lines.append(line)
                elif clean_lines:
                    clean_lines[-1] += " " + line
                else:
                    clean_lines.append(line)
            
            summary_points = []
            for item in clean_lines[:3]:
                # strip some brackets
                preview = item.replace("[Source", "Source").strip()
                summary_points.append(f"• {preview[:150]}...")
            
            points_str = "\n".join(summary_points)
            return (
                f"⚠️ **[Mock Mode - Gemini API Quota Exceeded]**\n\n"
                f"We successfully retrieved the most relevant context chunks from Milvus, but Gemini is rate-limited. "
                f"Here are the top matches found in your document database:\n\n{points_str}"
            )
        raise exc