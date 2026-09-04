"""OKF v0.2-shaped derived artifacts from extracted text.

Original source files are never written. Outputs are in-memory derived
extracts only. Structure inference is heuristic; ambiguous nodes are
flagged INCOMPLETE and need review.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.agents.enforcement.tokens import chunk_text, estimate_tokens

HEADING = re.compile(
    r"^(?:part\s+\d+|annex\s+\d+|§?\s*\d+(?:\.\d+)*|[A-Z][A-Z0-9 /-]{8,})$",
    re.IGNORECASE,
)


def clean_extracted_text(text: str) -> tuple[str, dict[str, int]]:
    lines = text.splitlines()
    stripped = 0
    kept: list[str] = []
    for line in lines:
        body = line.strip()
        if re.fullmatch(r"\d+|page\s+\d+|confidential|watermark", body, re.IGNORECASE):
            stripped += 1
            continue
        kept.append(re.sub(r"[ \t]+", " ", body))
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    return collapsed, {"linesStripped": stripped, "duplicatesRemoved": 0}


def build_okf_envelope(
    *,
    document_id: str,
    title: str,
    authority: str | None,
    text: str,
) -> dict[str, Any]:
    cleaned, stats = clean_extracted_text(text)
    nodes: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    order = 0
    for block in re.split(r"\n\s*\n+", cleaned):
        body = block.strip()
        if not body:
            continue
        first = body.split("\n", 1)[0].strip()
        is_heading = bool(HEADING.match(first)) and len(first) < 120
        if is_heading:
            order += 1
            node_id = f"n-{order:04d}"
            current = {
                "id": node_id,
                "type": "section",
                "label": first,
                "citation": first if re.search(r"§|\d", first) else None,
                "text": body,
                "parentId": "document-root",
                "order": order,
                "metadata": {
                    "keywords": [],
                    "normative": "shall" in body.lower() or "must" in body.lower(),
                },
            }
            nodes.append(current)
        elif current is not None:
            current["text"] = f"{current['text']}\n\n{body}"
        else:
            order += 1
            nodes.append(
                {
                    "id": f"n-{order:04d}",
                    "type": "topic",
                    "label": "Ungrouped extract",
                    "citation": None,
                    "text": body,
                    "parentId": "document-root",
                    "order": order,
                    "metadata": {"keywords": [], "normative": False, "status": "INCOMPLETE"},
                }
            )
    root = {
        "okfVersion": "0.2",
        "documentId": document_id,
        "title": title,
        "authority": authority,
        "documentClass": "Unknown",
        "effectiveDate": None,
        "jurisdiction": [],
        "language": "en",
        "cleaningStats": stats,
        "nodes": [
            {
                "id": "document-root",
                "type": "document",
                "label": title,
                "citation": None,
                "text": "",
                "parentId": None,
                "order": 0,
                "metadata": {"keywords": [], "normative": False},
            },
            *nodes,
        ],
        "reviewDisposition": "needs-review",
        "notes": [
            "Derived extract only; original source file was not modified.",
            "Structure inference is heuristic. SME/QA/RA review required.",
        ],
    }
    return root


def build_document_tree(okf: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, Any] = {}
    for item in okf["nodes"]:
        node_id = item["id"]
        nodes[node_id] = {
            "id": node_id,
            "parentId": item["parentId"],
            "children": [],
            "depth": 0 if item["parentId"] is None else 1,
            "path": f"/{item['id']}",
            "type": item["type"],
            "label": item["label"],
            "tokenEstimate": estimate_tokens(item.get("text") or ""),
            "okfRef": node_id,
        }
    for item in okf["nodes"]:
        parent = item["parentId"]
        if parent and parent in nodes:
            nodes[parent]["children"].append(item["id"])
    return {
        "treeId": hashlib.sha256(okf["documentId"].encode()).hexdigest()[:16],
        "rootId": "document-root",
        "nodes": nodes,
    }


def okf_chunks(okf: dict[str, Any], tree: dict[str, Any]) -> list[dict[str, Any]]:
    bodies = [
        node["text"] for node in okf["nodes"] if node["type"] != "document" and node.get("text")
    ]
    joined = "\n\n".join(bodies) if bodies else ""
    chunks, _removed = chunk_text(joined)
    for chunk in chunks:
        chunk["documentId"] = okf["documentId"]
        chunk["citation"] = okf.get("authority") or "needs-review"
        chunk["treePath"] = "/document-root"
        chunk["okfNodeIds"] = [node["id"] for node in okf["nodes"] if node["type"] != "document"][
            :8
        ]
        chunk["metadata"] = {
            "authority": okf.get("authority"),
            "documentClass": okf.get("documentClass"),
            "jurisdiction": okf.get("jurisdiction") or [],
            "normative": any(n.get("metadata", {}).get("normative") for n in okf["nodes"]),
        }
        tree_node = tree["nodes"].get(chunk["okfNodeIds"][0]) if chunk["okfNodeIds"] else None
        if tree_node:
            chunk["treePath"] = tree_node["path"]
    return chunks
