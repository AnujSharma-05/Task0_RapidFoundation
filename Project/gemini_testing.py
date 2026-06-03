import asyncio
from src.llm_service import generate_answer

async def main():
    response = await generate_answer(
        question="What is FastAPI?",
        context="""
FastAPI is a modern Python web framework.
"""
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())