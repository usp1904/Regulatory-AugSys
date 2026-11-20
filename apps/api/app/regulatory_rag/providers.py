"""Optional Vertex AI and Firestore adapters. Cloud SDKs load only when enabled."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


class ProviderConfigurationError(RuntimeError):
    """Raised when a requested cloud provider is not configured."""


class VertexEmbeddingProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.google_cloud_project:
            raise ProviderConfigurationError(
                "GOOGLE_CLOUD_PROJECT is required for Vertex embeddings"
            )
        try:
            from google import genai
            from google.genai.types import EmbedContentConfig
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Install the API rag optional dependencies"
            ) from exc
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        self._model = settings.rag_embedding_model
        self._dimensions = settings.rag_embedding_dimensions
        self._config_type = EmbedContentConfig

    def embed(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=self._model,
            contents=text,
            config=self._config_type(output_dimensionality=self._dimensions),
        )
        if not response.embeddings or not response.embeddings[0].values:
            raise RuntimeError("Vertex AI returned an empty embedding")
        return list(response.embeddings[0].values)


class FirestoreIndexStore:
    """Firestore-backed vector and adjacency index, separate from MARAS business tables."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.google_cloud_project:
            raise ProviderConfigurationError(
                "GOOGLE_CLOUD_PROJECT is required for Firestore"
            )
        try:
            from google.cloud import firestore
            from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Install the API rag optional dependencies"
            ) from exc
        self._firestore_module = firestore
        self._distance_measure = DistanceMeasure
        self._db = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database,
        )
        self._prefix = settings.rag_collection_prefix

    def upsert_chunk(self, chunk: dict[str, Any]) -> None:
        record = dict(chunk)
        if "embedding" in record:
            record["embedding"] = self._firestore_module.Vector(record["embedding"])
        self._db.collection(f"{self._prefix}_chunks").document(
            chunk["chunk_id"]
        ).set(record)

    def upsert_entity(self, entity: dict[str, Any]) -> None:
        self._db.collection(f"{self._prefix}_entities").document(
            entity["entity_id"]
        ).set(entity)

    def upsert_edge(self, edge: dict[str, Any]) -> None:
        self._db.collection(f"{self._prefix}_edges").document(
            edge["edge_id"]
        ).set(edge)

    def vector_search(self, vector: list[float], limit: int) -> list[dict[str, Any]]:
        query = self._db.collection(f"{self._prefix}_chunks").find_nearest(
            vector_field="embedding",
            query_vector=self._firestore_module.Vector(vector),
            distance_measure=self._distance_measure.COSINE,
            limit=limit,
            distance_result_field="vector_distance",
        )
        return [doc.to_dict() for doc in query.stream()]

    def get_related_edges(
        self, entity_ids: list[str], limit: int = 100
    ) -> list[dict[str, Any]]:
        if not entity_ids:
            return []
        collection = self._db.collection(f"{self._prefix}_edges")
        found: list[dict[str, Any]] = []
        for start in range(0, len(entity_ids), 10):
            batch = entity_ids[start : start + 10]
            query = collection.where("source_id", "in", batch).limit(limit)
            found.extend(doc.to_dict() for doc in query.stream())
        return found[:limit]
