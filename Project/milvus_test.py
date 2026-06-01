from src.milvus_store import milvus_store

client = milvus_store._get_client()

client.load_collection(
    collection_name="document_chunks"
)

results = client.search(
    collection_name="document_chunks",
    data=[[0.0] * 384],
    limit=3
)

print(results)