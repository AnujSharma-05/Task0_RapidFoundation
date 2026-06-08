from src.database import sessionLocal
from src.models import Document, DocumentChunk
from src.milvus_store import milvus_store

db = sessionLocal()

print("Documents:", db.query(Document).count())
print("Chunks:", db.query(DocumentChunk).count())

client = milvus_store._get_client()

print(
    "Milvus:",
    client.get_collection_stats(
        collection_name="document_chunks"
    )
)