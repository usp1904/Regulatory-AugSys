# MARAS Workflow Index

Schema: maras.workflows.v1
Harness: CRS (Caveman + RTK + Supermemory + Graphify)

| ID | Workflow | Graph | MVP |
|----|----------|-------|-----|
| WF-MVP-ASSURE | MARAS Assure (browser MVP) | Scope → Intake → Govern → Decompose → QC → Evidence → Export (DRAFT_NOT_CONTROLLED) | MVP-01, MVP-21 |
| WF-PLATFORM-INGEST | Controlled document ingestion | Upload → Hash → Parse → Store → Audit | MVP-22, MVP-23 |
| WF-PLATFORM-EVIDENCE | Evidence capture and human review | Capture → Pending → Review → Approved | Rejected | Needs clarification | MVP-23 |
| WF-PLATFORM-DOSSIER | Evidence-based dossier export | Approved evidence → CTD order → Render → Manifest → Immutable file → Audit | MVP-24 |
| WF-PLATFORM-CTD | CTD Module 3.2.S validation | Documents → Framework/Jurisdiction scope → Validate → Gap report | MVP-22 |
| WF-GLOBAL-COMPARE | Global regulation comparison | Topic → Market matrix → Diff → Co-op deliverable | MVP-16 |
| WF-READINESS | Inspection readiness | Regulation ↔ SOP map → Gap flags → Inspection pack → Download | MVP-17, MVP-18 |
| WF-PLATFORM-AGENTS | Agent harness auto-select and enforcement | Intent → Select harness → Authz → Guardrails → Chunk/dedup → Adapter → Audit | MVP-21, MVP-26 |