"""Evidence-linked regulatory entity and relationship extraction."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.regulatory_rag.chunking import RegulatoryChunk


@dataclass(frozen=True)
class GraphEntity:
    entity_id: str
    label: str
    entity_type: str


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str
    chunk_id: str
    evidence: str


_ENTITY_PATTERNS = {
    "REGULATION": re.compile(
        r"\b(?:21 CFR(?: Part)? \d+(?:\.\d+)?|EU GMP Annex \d+|ICH Q\d+[A-Z]?)\b",
        re.I,
    ),
    "CONTROL": re.compile(
        r"\b(?:access control|audit trail|electronic signature|change control|"
        r"validation|data integrity)\b",
        re.I,
    ),
    "PROCESS": re.compile(
        r"\b(?:batch record|deviation management|document control|CAPA|"
        r"training record|risk assessment)\b",
        re.I,
    ),
}


def extract_graph_facts(
    chunks: list[RegulatoryChunk],
) -> tuple[list[GraphEntity], list[GraphEdge]]:
    """Extract transparent candidate facts; every edge retains its source chunk."""
    entities: dict[str, GraphEntity] = {}
    edges: dict[str, GraphEdge] = {}
    for chunk in chunks:
        found: list[GraphEntity] = []
        for kind, pattern in _ENTITY_PATTERNS.items():
            for match in pattern.finditer(chunk.text):
                label = re.sub(r"\s+", " ", match.group(0)).strip()
                key = f"{kind}:{label.casefold()}"
                entity_id = hashlib.sha256(key.encode()).hexdigest()
                entity = GraphEntity(entity_id, label, kind)
                entities[entity_id] = entity
                found.append(entity)
        for source in found:
            for target in found:
                if source.entity_id == target.entity_id:
                    continue
                relation = "MENTIONED_WITH"
                edge_key = (
                    f"{source.entity_id}:{relation}:{target.entity_id}:{chunk.chunk_id}"
                )
                edge_id = hashlib.sha256(edge_key.encode()).hexdigest()
                edges[edge_id] = GraphEdge(
                    edge_id=edge_id,
                    source_id=source.entity_id,
                    target_id=target.entity_id,
                    relation=relation,
                    chunk_id=chunk.chunk_id,
                    evidence=chunk.text[:500],
                )
    return list(entities.values()), list(edges.values())
