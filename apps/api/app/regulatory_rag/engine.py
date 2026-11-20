"""Hybrid lexical, vector and provenance-linked graph retrieval engine."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.regulatory_rag.chunking import RegulatoryChunk, build_document_chunks
from app.regulatory_rag.graph import extract_graph_facts
from app.regulatory_rag.providers import FirestoreIndexStore, VertexEmbeddingProvider


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9._-]{1,}", text.casefold())


def _lexical_score(query: str, text: str) -> float:
    query_terms = set(_terms(query))
    if not query_terms:
        return 0.0
    counts = Counter(_terms(text))
    coverage = sum(bool(counts[term]) for term in query_terms) / len(query_terms)
    frequency = sum(min(counts[term], 2) for term in query_terms) / (
        2 * len(query_terms)
    )
    return round(0.85 * coverage + 0.15 * frequency, 4)


def _chunk_dict(chunk: RegulatoryChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_version": chunk.document_version,
        "file_hash": chunk.file_hash,
        "filename": chunk.filename,
        "page_number": chunk.page_number,
        "ordinal": chunk.ordinal,
        "heading": chunk.heading,
        "text": chunk.text,
    }


def index_document(db: Session, document_id: int) -> dict[str, Any]:
    document = db.get(Document, document_id)
    if document is None:
        raise ValueError("Source document not found")
    if document.parse_status != "EXTRACTED":
        raise ValueError("Document extraction must complete before RAG indexing")
    chunks = build_document_chunks(document)
    entities, edges = extract_graph_facts(chunks)
    settings = get_settings()
    indexed_vector_count = 0
    indexed_graph = False
    provider_status = "LOCAL_LEXICAL_ONLY"

    if settings.rag_enabled:
        embeddings = VertexEmbeddingProvider()
        store = FirestoreIndexStore()
        for chunk in chunks:
            record = _chunk_dict(chunk)
            record["embedding"] = embeddings.embed(chunk.text)
            record["pipeline_version"] = "maras-rag-v1"
            store.upsert_chunk(record)
            indexed_vector_count += 1
        for entity in entities:
            store.upsert_entity(entity.__dict__)
        for edge in edges:
            store.upsert_edge(edge.__dict__)
        indexed_graph = True
        provider_status = "VERTEX_FIRESTORE"

    return {
        "document_id": document.id,
        "document_version": document.version,
        "file_hash": document.file_hash,
        "chunk_count": len(chunks),
        "entity_count": len(entities),
        "edge_count": len(edges),
        "vector_count": indexed_vector_count,
        "graph_persisted": indexed_graph,
        "provider_status": provider_status,
    }


def retrieve_hybrid(
    db: Session, query: str, document_ids: list[int] | None, top_k: int
) -> dict[str, Any]:
    statement = (
        select(Document)
        .where(Document.parse_status == "EXTRACTED")
        .order_by(Document.id.desc())
    )
    if document_ids:
        statement = statement.where(Document.id.in_(document_ids))
    documents = db.scalars(statement).all()
    candidates: dict[str, dict[str, Any]] = {}
    local_chunks: list[RegulatoryChunk] = []
    for document in documents:
        for chunk in build_document_chunks(document):
            local_chunks.append(chunk)
            score = _lexical_score(query, chunk.text)
            if score:
                item = _chunk_dict(chunk)
                item.update(
                    {"lexical_score": score, "vector_score": 0.0, "graph_score": 0.0}
                )
                candidates[chunk.chunk_id] = item

    settings = get_settings()
    retrieval_mode = "LEXICAL_FALLBACK"
    if settings.rag_enabled:
        embedder = VertexEmbeddingProvider()
        store = FirestoreIndexStore()
        vector = embedder.embed(query)
        for item in store.vector_search(vector, max(top_k * 4, 20)):
            if document_ids and item.get("document_id") not in document_ids:
                continue
            distance = float(item.get("vector_distance", 1.0))
            item["vector_score"] = max(0.0, min(1.0, 1.0 - distance))
            item["lexical_score"] = _lexical_score(query, item.get("text", ""))
            item["graph_score"] = 0.0
            candidates[item["chunk_id"]] = item
        retrieval_mode = "HYBRID_VERTEX_FIRESTORE"

    # Reciprocal-rank fusion combines lexical and semantic candidate rankings.
    lexical_rank = sorted(
        candidates.values(), key=lambda item: item.get("lexical_score", 0), reverse=True
    )
    vector_rank = sorted(
        candidates.values(), key=lambda item: item.get("vector_score", 0), reverse=True
    )
    rrf: dict[str, float] = {}
    for ranking in (lexical_rank, vector_rank):
        for rank, item in enumerate(ranking, start=1):
            rrf[item["chunk_id"]] = rrf.get(item["chunk_id"], 0.0) + 1.0 / (60 + rank)

    # Graph facts are extracted from the same controlled source chunks.
    entities, edges = extract_graph_facts(local_chunks)
    query_terms = set(_terms(query))
    matched_entity_ids = [
        entity.entity_id
        for entity in entities
        if set(_terms(entity.label)) & query_terms
    ]
    related_chunk_ids = {
        edge.chunk_id
        for edge in edges
        if edge.source_id in matched_entity_ids or edge.target_id in matched_entity_ids
    }
    for chunk_id in related_chunk_ids:
        if chunk_id in candidates:
            candidates[chunk_id]["graph_score"] = 1.0
            rrf[chunk_id] = rrf.get(chunk_id, 0.0) + 1.0 / 61
    if related_chunk_ids:
        retrieval_mode += "_WITH_LOCAL_GRAPH_EXPANSION"

    ranked = sorted(
        candidates.values(), key=lambda item: rrf.get(item["chunk_id"], 0), reverse=True
    )
    results = []
    for item in ranked[:top_k]:
        results.append(
            {
                "document_id": item["document_id"],
                "filename": item["filename"],
                "document_version": item["document_version"],
                "file_hash": item["file_hash"],
                "location_type": "page" if item.get("page_number") else "chunk",
                "location": (
                    f"page:{item['page_number']}"
                    if item.get("page_number")
                    else f"chunk:{item['ordinal']}"
                ),
                "chunk_id": item["chunk_id"],
                "excerpt": item["text"][:1200],
                "lexical_score": item.get("lexical_score", 0.0),
                "vector_score": item.get("vector_score", 0.0),
                "graph_score": item.get("graph_score", 0.0),
                "fusion_score": round(rrf.get(item["chunk_id"], 0.0), 6),
            }
        )
    return {
        "status": "OK" if results else "NO_MATCH",
        "query": query,
        "retrieval_mode": retrieval_mode,
        "results": results,
        "message": (
            "Evidence passages retrieved. Scores rank retrieval candidates; "
            "they are not regulatory confidence."
            if results
            else "No evidence passages matched the query in the selected document scope."
        ),
    }
