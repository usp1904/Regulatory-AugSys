# Structured obligation normalization (MARAS)

**Status:** DRAFT_NOT_CONTROLLED — parse and impact hints only. Not a compliance determination.

## Purpose

MARAS normalizes modal regulatory language from **ingested excerpts only** (library `GXP_CHUNKS`, RAG `OBL-*` obligations, PBI `sourceRequirement` / `sourceExcerpt`) into structured obligations and linked impact records for the 19-stage trace pipeline.

## Schema (`maras.structured-obligation.v1`)

| Field | Description |
|-------|-------------|
| `modality` | `MUST` \| `SHALL` \| `REQUIRED_TO` \| `PROHIBITED` |
| `subject` | Who or what the clause addresses (parsed; may be needs-review) |
| `action` | Verb phrase after the modal |
| `object` | Target of the action when parseable |
| `sourceSpan` | Verbatim substring + `chunkId` / `regRef` / `sourceKind` |
| `confidence` | `low` \| `medium` — not a legal interpretation score |
| `needsReview` | Parse ambiguity or missing subject |

No obligations are invented when no modal phrasing appears in sources.

## Downstream impacts

For each structured obligation the generators produce:

1. **Compliance outcome** (`observable`, `measurementHint`, `sourceSupport[]`) — observable end-state language tied to quotes; gaps flagged `needs-review`.
2. **Business capability impact** (`capability`, `changeType`, `rationale`, `inferential`) — capability labels may be inferential when sources are silent; SME/QA review required.
3. **Value stream impact** (`stream`, `journeyPhase`, `touchpoints`, `lifecycleStage`, `sourceSupport`) — journey mapping when obligation wording supports it; otherwise needs-review.

## Pipeline integration

- `buildRegulatoryTraceChainForStory` attaches `structuredObligations` to the trace chain and populates stages `OBLIGATION`, `COMPLIANCE_OUTCOMES`, `BUSINESS_CAPABILITIES`, and `VALUE_STREAMS`.
- **Compliance Details** shows normalized obligation cards (default PBI three-question view unchanged).
- `DRAFT-MARAS-Human-Review-Package.json` includes `structuredObligationSchema` and per-story bundles.

## JSON Schema

See [structured-obligation-record.schema.json](./schemas/structured-obligation-record.schema.json).

## Review

Evidence indicates machine parsing can mis-split subjects or outcomes. **SME/QA/RA review** is required before baselining capability or value-stream fields marked inferential or needs-review.
