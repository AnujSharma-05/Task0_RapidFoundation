from src.milvus_store import milvus_store

client = milvus_store._get_client()

client.create_collection(
    collection_name="migration_test",
    dimension=384
)

print(client.list_collections())