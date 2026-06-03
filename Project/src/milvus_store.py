import os
import time
from typing import Any

from .config import (
    MILVUS_COLLECTION,
    EMBEDDING_DIM,
    MILVUS_URI,
)

from pymilvus import MilvusClient, DataType

print("milvus_store import started")

class MilvusStore:
    """Small Milvus wrapper to keep vector DB operations isolated."""

    def __init__(self) -> None:
        self.collection_name = MILVUS_COLLECTION
        self.dim = EMBEDDING_DIM
        self._client: MilvusClient | None = None

    def _get_client(self) -> MilvusClient:

        if self._client is not None:
            return self._client

        uri = os.getenv("MILVUS_URI")

        if not uri:
            raise RuntimeError(
                "MILVUS_URI is not configured"
            )

        print(
            f"CONNECTED TO MILVUS SERVER: {uri}"
        )

        token = os.getenv("MILVUS_TOKEN")

        self._client = MilvusClient(
            uri=uri,
            token=token,
        )

        return self._client

    def _create_collection(self, client: MilvusClient) -> None:
        schema = client.create_schema(
            auto_id=False,
            enable_dynamic_field=True
        )
        
        # Primary Key
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        # Vector Field
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self.dim)
        # Custom Scalar Fields
        schema.add_field(field_name="document_id", datatype=DataType.INT64)
        schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535)
        
        client.create_collection(
            collection_name=self.collection_name,
            schema=schema
        )
        
        # Prepare vector index
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE"
        )
        client.create_index(
            collection_name=self.collection_name,
            index_params=index_params
        )
        print(f"CREATED COLLECTION & INDEX: {self.collection_name}")

    def ensure_collection(self) -> None: 
        client = self._get_client()

        if not client.has_collection(collection_name=self.collection_name):
            self._create_collection(client)

        # Always ensure the collection is loaded into memory.
        # Attu's Data Explorer and any query() call requires the collection
        # to be in a Loaded state. Without this, Attu shows 'No data found'
        # even when data physically exists in the growing segment.
        client.load_collection(collection_name=self.collection_name)
        print(f"COLLECTION LOADED: {self.collection_name}")

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
        print(
                f"INSERTING {len(chunks)} CHUNKS"
            )
        result = client.insert(collection_name=self.collection_name, data=data)
        print(result)

        # Flush pushes the in-memory growing segment to sealed segments.
        # Without this, Attu's Data Explorer shows 'No data found' because
        # it only reads sealed (persisted) segments, not the write buffer.
        # Python client.query() reads both, which is why queries worked but
        # Attu showed nothing.
        client.flush(collection_name=self.collection_name)
        print(f"FLUSHED {len(chunks)} CHUNKS TO MILVUS")

        return [int(i) for i in result.get("ids", [])]

    def search(self, query_embedding: list[float], top_k: int = 5, document_id: int | None = None) -> list[dict[str, Any]]:
        self.ensure_collection()  # also loads the collection
        client = self._get_client()
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

    # def delete_all_chunks(self) -> None:
    #     client = self._get_client()

    #     if client.has_collection(
    #         collection_name=self.collection_name
    #     ):
    #         client.drop_collection(
    #             collection_name=self.collection_name
    #         )

    #     client.create_collection(
    #         collection_name=self.collection_name,
    #         dimension=self.dim,
    #     )

    def delete_all_chunks(self) -> None:

        print("MILVUS A")

        client = self._get_client()

        print("MILVUS B")

        if client.has_collection(
            collection_name=self.collection_name
        ):

            print("MILVUS C")

            client.drop_collection(
                collection_name=self.collection_name
            )

            print("MILVUS D")

        print("MILVUS E")

        self._create_collection(client)

        print("MILVUS F")

print("creating milvus_store singleton")

milvus_store = MilvusStore()

print("milvus_store singleton created")
