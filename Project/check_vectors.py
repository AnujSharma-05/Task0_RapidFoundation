from pymilvus import MilvusClient

client = MilvusClient(
    uri="http://localhost:19530"
)

rows = client.query(
    collection_name="document_chunks",
    filter="id > 0",
    limit=3,
)

print(rows)