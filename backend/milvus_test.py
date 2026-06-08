from pymilvus import MilvusClient

client = MilvusClient(
    uri="http://localhost:19530"
)

rows = client.query(
    collection_name="document_chunks",
    filter="id > 0",
    output_fields=["document_id", "chunk_index", "content"],
    limit=5
)

for row in rows:
    print(row)
    