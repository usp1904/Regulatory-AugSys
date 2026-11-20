"""Tests for MARAS Regulatory Intelligence and source-grounded RAG retrieval."""

from __future__ import annotations

import hashlib

from app.models.document import Document, DocumentPage
from app.regulatory_rag.chunking import build_document_chunks
from app.regulatory_rag.engine import retrieve_hybrid
from app.regulatory_rag.graph import extract_graph_facts
from app.schemas.regulatory_intelligence import RegulatoryRetrievalRequest
from app.services.regulatory_intelligence import retrieve_regulatory_evidence


def _add_document(db_session, text: str, *, filename: str = "regulation.pdf") -> Document:
    document = Document(
        filename=filename,
        content_type="application/pdf",
        byte_size=100,
        file_hash=hashlib.sha256(text.encode()).hexdigest(),
        storage_path=f"/tmp/{filename}",
        version=2,
        uploader="test",
        parse_status="EXTRACTED",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(DocumentPage(document_id=document.id, page_number=7, text_content=text))
    db_session.commit()
    db_session.refresh(document)
    return document


def test_retrieval_returns_exact_versioned_source_evidence(db_session) -> None:
    source = _add_document(
        db_session,
        "The system shall generate audit trail records for changes to regulated records.",
    )
    result = retrieve_regulatory_evidence(
        db_session,
        RegulatoryRetrievalRequest(query="audit trail regulated records", top_k=5),
    )
    assert result.status == "OK"
    assert len(result.results) == 1
    evidence = result.results[0]
    assert evidence.document_id == source.id
    assert evidence.document_version == 2
    assert evidence.file_hash == source.file_hash
    assert evidence.location == "page:7"
    assert "audit trail records" in evidence.excerpt


def test_retrieval_respects_document_scope(db_session) -> None:
    first = _add_document(
        db_session,
        "Electronic signatures shall be controlled.",
        filename="one.pdf",
    )
    _add_document(db_session, "Audit trails shall be reviewed.", filename="two.pdf")
    result = retrieve_regulatory_evidence(
        db_session,
        RegulatoryRetrievalRequest(query="electronic signatures", document_ids=[first.id]),
    )
    assert result.status == "OK"
    assert {item.document_id for item in result.results} == {first.id}


def test_retrieval_returns_no_match_without_inventing_evidence(db_session) -> None:
    _add_document(db_session, "The quality unit reviews batch records.")
    result = retrieve_regulatory_evidence(
        db_session,
        RegulatoryRetrievalRequest(query="quantum computing"),
    )
    assert result.status == "NO_MATCH"
    assert result.results == []


def test_retrieval_rejects_unextracted_documents(db_session) -> None:
    document = Document(
        filename="pending.pdf",
        content_type="application/pdf",
        byte_size=100,
        file_hash=hashlib.sha256(b"pending").hexdigest(),
        storage_path="/tmp/pending.pdf",
        version=1,
        uploader="test",
        parse_status="PENDING",
    )
    db_session.add(document)
    db_session.commit()
    result = retrieve_regulatory_evidence(
        db_session,
        RegulatoryRetrievalRequest(query="pending document"),
    )
    assert result.status == "NO_MATCH"


def test_chunk_ids_are_stable_and_retain_source_identity(db_session) -> None:
    document = _add_document(db_session, "21 CFR Part 11 requires audit trail controls. " * 30)
    first = build_document_chunks(document, max_chars=200, overlap=20)
    second = build_document_chunks(document, max_chars=200, overlap=20)
    assert first
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]
    assert all(item.file_hash == document.file_hash for item in first)


def test_graph_facts_keep_evidence_chunk_references(db_session) -> None:
    document = _add_document(
        db_session,
        "21 CFR Part 11 requires audit trail and electronic signature controls.",
    )
    chunks = build_document_chunks(document)
    entities, edges = extract_graph_facts(chunks)
    assert {entity.entity_type for entity in entities} >= {"REGULATION", "CONTROL"}
    assert edges
    assert all(edge.chunk_id in {chunk.chunk_id for chunk in chunks} for edge in edges)


def test_hybrid_retrieval_reports_lexical_mode_without_cloud_credentials(db_session) -> None:
    _add_document(db_session, "21 CFR Part 11 requires audit trail controls.")
    result = retrieve_hybrid(db_session, "audit trail controls", None, 5)
    assert result["status"] == "OK"
    assert result["retrieval_mode"].startswith("LEXICAL_FALLBACK")
    assert result["results"][0]["file_hash"]
