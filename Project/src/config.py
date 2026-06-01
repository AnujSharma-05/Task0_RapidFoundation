import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

MILVUS_LITE_DB = os.getenv(
    "MILVUS_LITE_DB",
    "milvus_demo.db"
)

MILVUS_COLLECTION = os.getenv(
    "MILVUS_COLLECTION",
    "document_chunks"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

EMBEDDING_DIM = int(
    os.getenv(
        "EMBEDDING_DIM",
        "384"
    )
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)