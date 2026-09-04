"""Agent harness auto-select and enforcement tests."""

from __future__ import annotations

from sqlalchemy import select

from app.agents.enforcement.tokens import estimate_tokens, optimize_tokens
from app.agents.okf_pipeline import build_document_tree, build_okf_envelope, okf_chunks
from app.agents.registry import HARNESS_REGISTRY
from app.agents.selector import infer_task_kind, select_harness
from app.agents.types import HarnessId, TaskKind
from app.models.audit_event import AuditEvent
from app.models.document import Document, DocumentPage


def _run(client, intent: str, **extra):
    body = {
        "intent": intent,
        "actor": "casey.reviewer",
        "role": "qa",
        "payload": extra.pop("payload", {}),
        **extra,
    }
    return client.post("/api/v1/agents/run", json=body)


def test_registry_lists_required_harnesses(client) -> None:
    response = client.get("/api/v1/agents/registry")
    assert response.status_code == 200
    ids = {item["harness_id"] for item in response.json()["harnesses"]}
    assert ids == {
        "deepseek_loop",
        "langgraph_langsmith_guardrails",
        "llamaindex_rag",
        "redis_membrane_htmx",
        "semantic_kernel",
        "transformerlab",
    }
    assert set(HARNESS_REGISTRY) == set(TaskKind)


def test_auto_select_maps_intents_to_harnesses() -> None:
    cases = [
        (
            "Iterate the CRS DeepSeek loop until QC passes",
            TaskKind.LOOP_ENGINEERING,
            HarnessId.DEEPSEEK_LOOP,
        ),
        (
            "LangGraph orchestration with Guardrails and LangSmith traces",
            TaskKind.ORCHESTRATION_COMPLIANCE,
            HarnessId.LANGGRAPH_LANGSMITH_GUARDRAILS,
        ),
        (
            "Build LlamaIndex RAG with OKF chunking and retrieval",
            TaskKind.RAG,
            HarnessId.LLAMAINDEX_RAG,
        ),
        ("Stand up Redis Membrane HTMX infra cache", TaskKind.INFRA, HarnessId.REDIS_MEMBRANE_HTMX),
        (
            "Semantic Kernel skill orchestration for citation plugins",
            TaskKind.SKILL_ORCHESTRATION,
            HarnessId.SEMANTIC_KERNEL,
        ),
        (
            "TransformerLab idea-to-app conversion for a review queue",
            TaskKind.IDEA_TO_APP,
            HarnessId.TRANSFORMERLAB,
        ),
    ]
    for intent, kind, harness in cases:
        inferred, signals = infer_task_kind(intent)
        assert inferred is kind, intent
        assert signals
        selected = select_harness(intent)
        assert selected.harness_id is harness


def test_explicit_task_kind_overrides_inference() -> None:
    selected = select_harness(
        "retrieve OKF chunks for RAG", explicit_kind=TaskKind.LOOP_ENGINEERING
    )
    assert selected.task_kind is TaskKind.LOOP_ENGINEERING
    assert selected.inferred_kind is TaskKind.RAG
    assert selected.harness_id is HarnessId.DEEPSEEK_LOOP


def test_select_endpoint(client) -> None:
    response = client.post(
        "/api/v1/agents/select",
        json={"intent": "LlamaIndex RAG with semantic chunking"},
    )
    assert response.status_code == 200
    assert response.json()["selection"]["harness_id"] == "llamaindex_rag"


def test_run_blocks_unknown_actor(client) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={"intent": "LangGraph orchestration", "actor": "unknown", "role": "qa"},
    )
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"]


def test_denied_run_writes_audit_event(client, db_session) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={"intent": "Redis cache infra", "actor": "guest", "role": "qa"},
    )
    assert response.status_code == 403
    events = db_session.scalars(
        select(AuditEvent).where(AuditEvent.event_type == "agent_run_denied")
    ).all()
    assert events
    assert "Unauthorized" in (events[0].detail or "")


def test_run_blocks_unlisted_role(client) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={"intent": "DeepSeek loop engineering", "actor": "casey", "role": "extern"},
    )
    assert response.status_code == 403


def test_guardrails_reject_forbidden_claims(client) -> None:
    response = _run(client, "Make the dossier inspection-ready via LangGraph")
    assert response.status_code == 422
    assert "forbidden" in response.json()["detail"].lower()


def test_external_send_blocked_by_data_governance(client) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={
            "intent": "LlamaIndex RAG over extracts",
            "actor": "casey.reviewer",
            "role": "ra",
            "send_external": True,
            "payload": {"text": "Section 11.10 records shall be retained."},
        },
    )
    assert response.status_code == 403
    assert "External transmission" in response.json()["detail"]


def test_rag_requires_derived_text(client) -> None:
    response = _run(client, "LlamaIndex RAG retrieval without a corpus")
    assert response.status_code == 422
    assert "payload.text" in response.json()["detail"]


def test_successful_runs_each_harness_and_audit(client, db_session) -> None:
    corpus = (
        "Part 11 Electronic Records\n\n"
        + ("Persons who use electronic records shall employ procedures. " * 80)
        + "\n\n§11.10 Controls for closed systems\n\n"
        + ("The system shall generate an accurate and complete copy. " * 80)
    )
    payloads = [
        ("Iterate the CRS DeepSeek loop until QC passes", {}),
        ("LangGraph orchestration with Guardrails schema checks", {}),
        (
            "LlamaIndex RAG with OKF semantic chunking",
            {"payload": {"text": corpus, "authority": "FDA"}},
        ),
        (
            "Redis Membrane HTMX infra for /api/v1/agents/run",
            {"payload": {"route": "/api/v1/agents/run"}},
        ),
        ("Semantic Kernel skill orchestration for citation plugins", {}),
        (
            "TransformerLab idea-to-app conversion for a review queue",
            {"payload": {"idea": "Draft review queue"}},
        ),
    ]
    for intent, extra in payloads:
        response = _run(client, intent, **extra)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["enforcement"]["schema_valid"] is True
        assert body["enforcement"]["authorized"] is True
        assert body["enforcement"]["audit_event_id"]
        assert body["review_disposition"] == "needs-review"
        assert body["output"]["harness_id"] == body["selection"]["harness_id"]
        tokens = body["enforcement"]["token_optimization"]
        assert tokens["chunks"] >= 1
    events = db_session.scalars(
        select(AuditEvent).where(AuditEvent.event_type == "agent_run")
    ).all()
    assert len(events) == len(payloads)


def test_rag_uses_document_extract_not_original_path(client, db_session) -> None:
    document = Document(
        filename="source.txt",
        content_type="text/plain",
        byte_size=100,
        file_hash="a" * 64,
        storage_path="/immutable/originals/source.txt",
        version=1,
        uploader="casey.reviewer",
        parse_status="EXTRACTED",
        text_excerpt="unused excerpt",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(
        DocumentPage(
            document_id=document.id,
            page_number=1,
            text_content=("Clause 12 systems shall retain audit trails. " * 120),
        )
    )
    db_session.commit()
    response = _run(
        client,
        "Retrieve OKF chunks for LlamaIndex RAG",
        document_id=document.id,
    )
    assert response.status_code == 200, response.text
    assert response.json()["output"]["okfVersion"] == "0.2"
    assert "original source files were not modified" in " ".join(response.json()["notes"]).lower()


def test_infra_membrane_denies_unknown_route(client) -> None:
    response = _run(
        client,
        "Redis Membrane HTMX infra probe",
        payload={"route": "/admin/secrets"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["output"]["membrane"]["allowed"] is False
    assert body["output"]["status"] == "blocked-local"


def test_token_dedup_and_chunk_bounds() -> None:
    paragraph = "Electronic signatures shall be unique to one individual. "
    text = (paragraph * 40 + "\n\n") * 3
    text = text + "\n\n" + paragraph * 40
    optimized, chunks, report = optimize_tokens(text)
    assert report.duplicates_removed >= 1
    assert optimized
    assert chunks
    for chunk in chunks:
        assert 1 <= chunk["tokenCount"] <= 1100
        assert estimate_tokens(chunk["text"]) == chunk["tokenCount"]


def test_okf_envelope_is_derived_and_versioned() -> None:
    text = (
        "Part 11\n\nPersons shall employ controls.\n\n§11.10\n\n"
        "Closed systems shall retain records after SME review."
    )
    okf = build_okf_envelope(document_id="doc-1", title="Extract", authority="FDA", text=text)
    assert okf["okfVersion"] == "0.2"
    tree = build_document_tree(okf)
    assert tree["rootId"] == "document-root"
    chunks = okf_chunks(okf, tree)
    assert chunks
    assert all("citation" in chunk for chunk in chunks)
