"""Tests for MARAS Regulatory Intelligence and source-grounded RAG retrieval."""

from __future__ import annotations

import hashlib

from app.models.document import Document, DocumentPage
from app.models.regulatory_truth import RegulatorySourceRecord
from app.regulatory_rag.chunking import build_document_chunks
from app.regulatory_rag.engine import index_document, retrieve_hybrid
from app.regulatory_rag.graph import extract_graph_facts
from app.regulatory_rag.index_store import LocalIndexStore
from app.regulatory_rag.sparse import bm25_scores, term_frequencies
from app.regulatory_rag.synthesis import build_evidence_answer
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
    assert result["retrieval_mode"].startswith("BM25_LIVE_FALLBACK")
    assert result["results"][0]["file_hash"]



def test_local_index_persists_and_retrieves_without_cloud(
    db_session, tmp_path, monkeypatch
) -> None:
    import app.regulatory_rag.engine as engine

    source = _add_document(
        db_session,
        "21 CFR Part 11 requires audit trail controls and electronic signatures.",
    )
    local_store = LocalIndexStore(tmp_path / "regulatory-index.sqlite3")
    monkeypatch.setattr(engine, "_local_store", lambda: local_store)

    indexed = index_document(db_session, source.id)
    assert indexed["provider_status"] == "LOCAL_SQLITE_BM25_GRAPH"
    assert indexed["graph_persisted"] is True
    assert indexed["vector_count"] == 0
    assert local_store.stats(source.id)["chunk_count"] > 0

    result = retrieve_hybrid(db_session, "21 CFR Part 11 audit trail", [source.id], 5)
    assert result["status"] == "OK"
    assert result["retrieval_mode"].startswith("LOCAL_SQLITE_BM25_GRAPH")
    assert result["results"][0]["document_id"] == source.id


def test_local_index_ignores_stale_document_versions(
    db_session, tmp_path, monkeypatch
) -> None:
    import app.regulatory_rag.engine as engine

    source = _add_document(db_session, "Audit trail controls are required.")
    local_store = LocalIndexStore(tmp_path / "regulatory-index.sqlite3")
    monkeypatch.setattr(engine, "_local_store", lambda: local_store)
    index_document(db_session, source.id)

    source.version = 3
    source.file_hash = hashlib.sha256(b"new version").hexdigest()
    db_session.commit()

    result = retrieve_hybrid(db_session, "audit trail controls", [source.id], 5)
    assert result["status"] == "OK"
    assert result["retrieval_mode"].startswith("BM25_LIVE_FALLBACK")
    assert all(item["document_version"] == 3 for item in result["results"])


def test_bm25_prefers_chunks_with_more_relevant_terms() -> None:
    documents = [
        {
            "chunk_id": "relevant",
            "text": "audit trail controls audit trail controls",
            "term_vector": term_frequencies("audit trail controls audit trail controls"),
        },
        {
            "chunk_id": "weak",
            "text": "general quality documentation",
            "term_vector": term_frequencies("general quality documentation"),
        },
    ]
    scores = bm25_scores("audit trail controls", documents)
    assert scores["relevant"] > scores["weak"]



def test_extractive_synthesis_only_returns_verbatim_cited_source_sentences() -> None:
    evidence = {
        "document_id": 42,
        "filename": "regulation.pdf",
        "document_version": 3,
        "file_hash": "a" * 64,
        "location": "page:12",
        "chunk_id": "chunk-abc",
        "source_status": "VERIFIED",
        "excerpt": (
            "The system shall maintain audit trail controls for regulated records. "
            "Personnel must complete assigned training before performing the activity."
        ),
    }
    answer = build_evidence_answer("audit trail controls", [evidence])
    assert answer["validation_status"] == "PASSED"
    assert answer["answer_mode"] == "EXTRACTIVE_EVIDENCE_ONLY"
    assert len(answer["claims"]) == 1
    claim = answer["claims"][0]
    assert claim["text"] in evidence["excerpt"]
    assert claim["citations"][0]["document_id"] == evidence["document_id"]
    assert claim["citations"][0]["chunk_id"] == evidence["chunk_id"]
    assert claim["citations"][0]["source_status"] == "VERIFIED"


def test_extractive_synthesis_abstains_when_no_sentence_matches() -> None:
    answer = build_evidence_answer(
        "quantum computing",
        [
            {
                "document_id": 1,
                "filename": "source.pdf",
                "document_version": 1,
                "file_hash": "b" * 64,
                "location": "page:1",
                "chunk_id": "chunk-1",
                "source_status": "VERIFIED",
                "excerpt": "Audit trail records shall be reviewed periodically.",
            }
        ],
    )
    assert answer["validation_status"] == "ABSTAINED"
    assert answer["claims"] == []



def test_unverified_regulatory_source_is_retrievable_but_not_synthesized(
    db_session,
) -> None:
    source = _add_document(
        db_session,
        "The system shall maintain audit trail controls for regulated records.",
    )
    db_session.add(
        RegulatorySourceRecord(
            document_id=source.id,
            title="Test regulation",
            issuing_authority="Test authority",
            jurisdiction="Test jurisdiction",
            document_type="Regulation",
            official_url="https://example.org/regulation",
            version_label="1",
            applicability_scope="Test scope",
            content_hash=source.file_hash,
            source_status="UNVERIFIED",
            created_by="test",
        )
    )
    db_session.commit()

    result = retrieve_hybrid(db_session, "audit trail controls", [source.id], 5)
    assert result["status"] == "OK"
    assert result["results"][0]["source_status"] == "UNVERIFIED"
    answer = build_evidence_answer("audit trail controls", result["results"])
    assert answer["validation_status"] == "ABSTAINED"
    assert answer["claims"] == []


def test_verified_regulatory_source_can_be_used_for_extractive_synthesis(
    db_session,
) -> None:
    source = _add_document(
        db_session,
        "The system shall maintain audit trail controls for regulated records.",
    )
    db_session.add(
        RegulatorySourceRecord(
            document_id=source.id,
            title="Verified test regulation",
            issuing_authority="Test authority",
            jurisdiction="Test jurisdiction",
            document_type="Regulation",
            official_url="https://example.org/verified-regulation",
            version_label="1",
            applicability_scope="Test scope",
            content_hash=source.file_hash,
            source_status="VERIFIED",
            created_by="test",
            verified_by="reviewer",
        )
    )
    db_session.commit()

    result = retrieve_hybrid(db_session, "audit trail controls", [source.id], 5)
    answer = build_evidence_answer("audit trail controls", result["results"])
    assert result["results"][0]["source_status"] == "VERIFIED"
    assert answer["validation_status"] == "PASSED"
    assert answer["claims"][0]["citations"][0]["document_id"] == source.id



def test_stale_source_hash_is_flagged_and_synthesis_abstains(db_session) -> None:
    source = _add_document(
        db_session,
        "The system shall maintain audit trail controls for regulated records.",
    )
    db_session.add(
        RegulatorySourceRecord(
            document_id=source.id,
            title="Previously verified regulation",
            issuing_authority="Test authority",
            jurisdiction="Test jurisdiction",
            document_type="Regulation",
            official_url="https://example.org/regulation",
            version_label="Previous version",
            applicability_scope="Test scope",
            content_hash=source.file_hash,
            source_status="VERIFIED",
            created_by="test",
            verified_by="reviewer",
        )
    )
    db_session.commit()

    source.file_hash = hashlib.sha256(b"new changed content").hexdigest()
    source.version = 3
    db_session.commit()

    result = retrieve_hybrid(db_session, "audit trail controls", [source.id], 5)
    assert result["results"][0]["source_status"] == "STALE"
    answer = build_evidence_answer("audit trail controls", result["results"])
    assert answer["validation_status"] == "ABSTAINED"
    assert answer["claims"] == []

def test_engine_status_reports_local_mode_when_cloud_is_disabled(monkeypatch):
    import app.regulatory_rag.engine as engine

    settings = engine.get_settings()
    monkeypatch.setattr(settings, "rag_enabled", False)
    monkeypatch.setattr(settings, "google_cloud_project", "")
    monkeypatch.setattr(engine, "get_settings", lambda: settings)
    status = engine.get_engine_status()
    assert status["engine"] == "MARAS_INTELLIGENT_HYBRID_GRAPH_RAG"
    assert status["active_retrieval_mode"] == "BM25_LOCAL_CANDIDATE_GRAPH"
    assert status["capabilities"]["llm_grounded_generation"] is False
    assert status["capabilities"]["multimodal_ocr_and_layout_extraction"] is False
