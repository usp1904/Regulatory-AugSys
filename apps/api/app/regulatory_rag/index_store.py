"""Zero-cost persistent local index using the Python standard-library SQLite engine."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.regulatory_rag.chunking import RegulatoryChunk
from app.regulatory_rag.graph import GraphEdge, GraphEntity


class LocalIndexStore:
    """Persist chunks, sparse term vectors and provenance-linked graph facts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    document_version INTEGER NOT NULL,
                    file_hash TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    page_number INTEGER,
                    ordinal INTEGER NOT NULL,
                    heading TEXT NOT NULL,
                    text TEXT NOT NULL,
                    term_vector TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_rag_chunks_document
                    ON rag_chunks(document_id, document_version, file_hash);
                CREATE TABLE IF NOT EXISTS rag_entities (
                    entity_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    entity_type TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rag_edges (
                    edge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    evidence TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_rag_edges_source ON rag_edges(source_id);
                CREATE INDEX IF NOT EXISTS ix_rag_edges_target ON rag_edges(target_id);
                CREATE INDEX IF NOT EXISTS ix_rag_edges_chunk ON rag_edges(chunk_id);
                """
            )

    def replace_document(
        self,
        document_id: int,
        chunks: list[RegulatoryChunk],
        entities: list[GraphEntity],
        edges: list[GraphEdge],
        term_vectors: dict[str, dict[str, float]],
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                DELETE FROM rag_edges
                WHERE chunk_id IN (
                    SELECT chunk_id FROM rag_chunks WHERE document_id = ?
                )
                """,
                (document_id,),
            )
            connection.execute("DELETE FROM rag_chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT OR REPLACE INTO rag_chunks
                (chunk_id, document_id, document_version, file_hash, filename,
                 page_number, ordinal, heading, text, term_vector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.document_version,
                        chunk.file_hash,
                        chunk.filename,
                        chunk.page_number,
                        chunk.ordinal,
                        chunk.heading,
                        chunk.text,
                        json.dumps(term_vectors.get(chunk.chunk_id, {}), sort_keys=True),
                    )
                    for chunk in chunks
                ],
            )
            connection.executemany(
                """
                INSERT OR REPLACE INTO rag_entities(entity_id, label, entity_type)
                VALUES (?, ?, ?)
                """,
                [(item.entity_id, item.label, item.entity_type) for item in entities],
            )
            connection.executemany(
                """
                INSERT OR REPLACE INTO rag_edges
                (edge_id, source_id, target_id, relation, chunk_id, evidence)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.edge_id,
                        item.source_id,
                        item.target_id,
                        item.relation,
                        item.chunk_id,
                        item.evidence,
                    )
                    for item in edges
                ],
            )

    def list_chunks(
        self, document_versions: dict[int, tuple[int, str]]
    ) -> list[dict[str, Any]]:
        if not document_versions:
            return []
        ids = list(document_versions)
        placeholders = ",".join("?" for _ in ids)
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM rag_chunks WHERE document_id IN ({placeholders})",
                ids,
            ).fetchall()
        return [
            dict(row)
            for row in rows
            if document_versions.get(row["document_id"])
            == (row["document_version"], row["file_hash"])
        ]

    def list_edges(self, entity_ids: list[str], chunk_ids: list[str]) -> list[dict[str, Any]]:
        if not entity_ids or not chunk_ids:
            return []
        bounded_entity_ids = entity_ids[:500]
        placeholders = ",".join("?" for _ in bounded_entity_ids)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM rag_edges
                WHERE source_id IN ({placeholders})
                   OR target_id IN ({placeholders})
                LIMIT 2000
                """,
                [*bounded_entity_ids, *bounded_entity_ids],
            ).fetchall()
        allowed_chunks = set(chunk_ids)
        return [dict(row) for row in rows if row["chunk_id"] in allowed_chunks]

    def stats(self, document_id: int) -> dict[str, int]:
        with self._connection() as connection:
            chunks = connection.execute(
                "SELECT COUNT(*) FROM rag_chunks WHERE document_id = ?", (document_id,)
            ).fetchone()[0]
            edges = connection.execute(
                """
                SELECT COUNT(*) FROM rag_edges
                WHERE chunk_id IN (SELECT chunk_id FROM rag_chunks WHERE document_id = ?)
                """,
                (document_id,),
            ).fetchone()[0]
        return {"chunk_count": int(chunks), "edge_count": int(edges)}
