from src.llm_service import generate_answer

response = generate_answer(
    question="What is FastAPI?",
    context="""
FastAPI is a modern Python web framework.
"""
)

print(response)