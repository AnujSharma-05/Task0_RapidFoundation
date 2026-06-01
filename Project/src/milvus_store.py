import os
import time
from typing import Any

from pymilvus import MilvusClient

lite_db_path = os.getenv("MILVUS_LITE_DB", "milvus_demo.db")

print("MILVUS FILE =", os.path.abspath(lite_db_path))

class MilvusStore:
    """Small Milvus wrapper to keep vector DB operations isolated."""

    def __init__(self) -> None:
        self.collection_name = os.getenv("MILVUS_COLLECTION", "document_chunks")
        self.dim = int(os.getenv("EMBEDDING_DIM", "384"))
        self._client: MilvusClient | None = None

    def _get_client(self) -> MilvusClient:
        if self._client is not None:
            return self._client

        uri = os.getenv("MILVUS_URI")
        if uri:
            token = os.getenv("MILVUS_TOKEN")
            self._client = MilvusClient(uri=uri, token=token)
            return self._client

        lite_db_path = os.getenv("MILVUS_LITE_DB", "milvus_demo.db")
        self._client = MilvusClient(lite_db_path)
        return self._client

    def ensure_collection(self) -> None:
        client = self._get_client()

        if client.has_collection(collection_name=self.collection_name):
            return

        client.create_collection(collection_name=self.collection_name, dimension=self.dim)

    def upsert_chunks(self, document_id: int, chunks: list[str], embeddings: list[list[float]]) -> list[int]:
        self.ensure_collection()
        client = self._get_client()

        base_id = time.time_ns()
        data = [
            {
                "id": int(base_id + idx),
                "vector": embeddings[idx],
                "document_id": document_id,
                "chunk_index": idx,
                "content": chunks[idx],
            }
            for idx in range(len(chunks))
        ]
        result = client.insert(collection_name=self.collection_name, data=data)
        return [int(i) for i in result.get("ids", [])]

    def search(self, query_embedding: list[float], top_k: int = 5, document_id: int | None = None) -> list[dict[str, Any]]:
        self.ensure_collection()
        client = self._get_client()
        client.load_collection(collection_name=self.collection_name)
        search_kwargs: dict[str, Any] = {
            "collection_name": self.collection_name,
            "data": [query_embedding],
            "limit": top_k,
            "output_fields": ["document_id", "chunk_index", "content"],
        }
        if document_id is not None:
            search_kwargs["filter"] = f"document_id == {document_id}"

        results = client.search(**search_kwargs)

        formatted: list[dict[str, Any]] = []
        for hit in results[0]:
            entity = hit.get("entity", {})
            formatted.append(
                {
                    "milvus_id": int(hit.get("id")),
                    "score": float(hit.get("distance", 0.0)),
                    "document_id": int(entity.get("document_id")),
                    "chunk_index": int(entity.get("chunk_index")),
                    "content": str(entity.get("content")),
                }
            )
        return formatted

    def delete_document_chunks(self, document_id: int) -> None:
        self.ensure_collection()
        client = self._get_client()
        client.delete(collection_name=self.collection_name, filter=f"document_id == {document_id}")


milvus_store = MilvusStore()
