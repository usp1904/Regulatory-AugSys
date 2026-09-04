"""LlamaIndex-shaped RAG adapter over derived extracts.

Never reads or mutates original stored files. Uses OKF v0.2 conversion and
semantic chunking from the local pipeline.
"""

from __future__ import annotations

from typing import Any

from app.agents.okf_pipeline import build_document_tree, build_okf_envelope, okf_chunks
from app.agents.types import AgentTaskRequest, HarnessId, SelectionResult


class LlamaIndexRagAdapter:
    harness_id = HarnessId.LLAMAINDEX_RAG

    def execute(
        self,
        *,
        request: AgentTaskRequest,
        selection: SelectionResult,
        optimized_text: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        document_id = str(
            request.document_id or request.payload.get("document_key") or "derived-extract"
        )
        title = str(request.payload.get("title") or "Derived extract")
        authority = request.payload.get("authority")
        if authority is not None:
            authority = str(authority)
        okf = build_okf_envelope(
            document_id=document_id,
            title=title,
            authority=authority,
            text=optimized_text,
        )
        tree = build_document_tree(okf)
        rag_chunks = okf_chunks(okf, tree)
        query = str(request.payload.get("query") or request.intent)
        hits = [
            {
                "chunkId": chunk["chunkId"],
                "citation": chunk.get("citation"),
                "treePath": chunk.get("treePath"),
                "tokenCount": chunk.get("tokenCount"),
                "excerpt": (chunk.get("text") or "")[:280],
            }
            for chunk in rag_chunks[:6]
        ]
        return {
            "status": "completed-local",
            "harness_id": self.harness_id.value,
            "review_disposition": "needs-review",
            "llamaindex": {
                "mode": "local-vectorless-index",
                "vendor_mapping": "LlamaIndex",
                "nodes": len(okf["nodes"]),
                "chunks": len(rag_chunks),
            },
            "okfVersion": okf["okfVersion"],
            "query": query,
            "hits": hits,
            "graph": selection.spec.graph,
            "notes": [
                "Indexed derived text only; original source files were not modified.",
                "No embeddings were sent to an external API.",
                "Citations and excerpts are machine-generated summaries; "
                "SME/QA/RA review required.",
            ],
        }
