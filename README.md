# MARAS v6.4.1 MVP

MARAS is a stakeholder-review MVP for Pharma and Life Sciences teams. It converts a scoped set of curated regulatory control summaries into a draft assurance package containing regulatory work items, acceptance criteria, risk context, evidence needs, and Jira/ADO/JSON exports.

## Regulatory-AugSys monorepo (local-first platform)

A new **Next.js + FastAPI** stack lives under `apps/` for CTD/eCTD CMC evidence management. The legacy single-file demo (`index.html`) remains the GitHub Pages MVP until the platform replaces it.

**Mandatory product principles** (full text): [`docs/prompts/cursor_master_prompt.md`](docs/prompts/cursor_master_prompt.md)

### Prerequisites

- Docker and Docker Compose **or** local Node 22+, Python 3.12+, PostgreSQL 16 (optional SQLite fallback)
- Copy environment template: `cp .env.example .env`

### Run everything with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web (Next.js health page) | http://localhost:3000 |
| Web CTD/eCTD Engine | http://localhost:3000/ctd |
| API (FastAPI `/health`) | http://localhost:8000/health |
| API CTD sections | `GET /api/v1/ctd-sections` |
| API document store | `POST /api/v1/documents`, `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `GET /api/v1/documents/{id}/download` |
| API evidence | `POST /api/v1/evidence`, `GET /api/v1/evidence`, `PATCH /api/v1/evidence/{id}`, `POST /api/v1/evidence/{id}/review`, `GET /api/v1/evidence/{id}/review-context`, `GET /api/v1/evidence/export` |
| API dossier export | `POST /api/v1/dossiers/{dossier_id}/export`, `GET /api/v1/dossier-exports/{export_id}`, `GET /api/v1/dossier-exports/{export_id}/download` |
| API CTD validation | `POST /api/v1/ctd-engine/validate` |
| PostgreSQL | `localhost:5432` (user/db: `regulatory` / `regulatory_augsys`) |

Run database migrations inside the API container:

```bash
docker compose exec api alembic upgrade head
```

### Run API locally (SQLite, no Docker)

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mkdir -p data
export DATABASE_URL=sqlite:///./data/regulatory_augsys.db
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
pytest
ruff check app tests
```

### Run API locally (PostgreSQL)

```bash
# Start Postgres (Docker example)
docker run --rm -d --name regulatory-pg \
  -e POSTGRES_USER=regulatory \
  -e POSTGRES_PASSWORD=regulatory \
  -e POSTGRES_DB=regulatory_augsys \
  -p 5432:5432 postgres:16-alpine

cd apps/api
source .venv/bin/activate  # after venv + pip install as above
export DATABASE_URL=postgresql+psycopg://regulatory:regulatory@localhost:5432/regulatory_augsys
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Run web locally

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000 — the health page shows web status and polls the API. Evidence review UI: `/evidence/review/{id}` (side-by-side source text and review form). Capture evidence from `/documents/{id}`.

```bash
npm run typecheck
npm run lint
npm run build
```

### Monorepo layout

```text
apps/api/     FastAPI, SQLAlchemy 2, Alembic
apps/web/     Next.js, TypeScript, Tailwind, shadcn/ui (Card)
docs/prompts/ Cursor master prompt and slice guidance
docker-compose.yml
```

---

## Intended stakeholders

- Regulatory Affairs and Compliance: applicability, jurisdiction, and source review.
- Quality Assurance: control, evidence, and approval review.
- Validation/CSA/CSV teams: test obligations and traceability.
- System Owners and Business Analysts: system context and business process fit.
- Product Owners and delivery teams: reviewed backlog export and sequencing.
- Internal Audit: traceability and outstanding clarification review.

## Safe MVP workflow

1. Select the regulated system type, Pharma/Life Sciences domain, jurisdiction, and source scope.
2. Define a measurable business outcome and compliance requirement.
3. Generate a draft package in Demo mode. Use **Quick demo** for the controlled LIMS/Part 11 scenario.
4. Review the captured public-source excerpt, version metadata, and authoritative link; items remain `SME_PENDING` until approval occurs in a controlled system.
5. Enter reviewer name, role, and comment, then record **SME review attested (draft)**, **Clarify**, or **N/A**.
6. Export the watermarked draft. Jira, ADO, FDA-schema, and JSON exports remain `DRAFT_NOT_CONTROLLED` regardless of browser review status.

**Consulting / strategy co-operations:** open the **Global Compare** tab to review the same control topic across markets (matrix, gap analysis, client briefing), export a draft matrix, or push harmonisation gaps into the Assure tab.

## Important limitations

- Generated content is a draft, not regulatory or legal advice.
- Public FDA/eCFR demo controls include captured excerpts and source-version metadata. These are still pending SME approval and are not controlled copies.
- Licensed GAMP 5 and ISO content is excluded from generation until a customer-controlled licensed source is available.
- Regulatory and requirement file inputs are enabled. TXT/CSV/JSON are parsed and SHA-256 hashed in the browser. PDF/Office binaries are accepted then **held**. Ingested regulatory files drive generation only after the production gate: official URL, authority, document class, effective date, capture date, file hash, license tag, and `SME_APPROVED`. Licensed standards remain blocked. Packages stay `DRAFT_NOT_CONTROLLED`.
- Saved packages use browser local storage and are not controlled records. Export JSON into the organisation's approved document repository for retention.
- Live AI is an experimental bring-your-own-key browser integration. It sends entered context directly to the selected provider. Do not use confidential, patient-identifiable, personal, or proprietary regulated data.
- Native Jira creation, RBAC, electronic signatures, immutable audit trails, malware scanning of uploads, live official-source re-validation, and regulatory change monitoring are phased capabilities and are intentionally not claimed by this MVP.

## Requirement-to-test traceability (RTK)

| ID | MVP requirement | Verification |
|---|---|---|
| MVP-01 | Block generation without system, domain, jurisdiction, outcome, sources, and requirement | Blank-submit browser test displays an accessible error summary |
| MVP-02 | Keep the Pharma LIMS sample in relevant control categories | Quick demo produces applicable public-source controls; medical-device-only and licensed sources are excluded |
| MVP-03 | Do not present automated scoring as regulatory approval | Output is labelled Draft; missing SME source approval forces Grade REVIEW and zero automated passes |
| MVP-04 | Provide authoritative-source navigation | Every Quick-demo PBI contains an official/public or publisher source link |
| MVP-05 | Produce readable business requirements | Regression test rejects known `must attributable`/noun-phrase grammar defects |
| MVP-06 | Preserve accountable draft review decisions | Each PBI records reviewer name, role, comment, timestamp and append-only-in-session history; exports include the fields |
| MVP-07 | Prevent rendered input/model content from executing HTML | Browser injection regression confirms escaped text and no script/image execution |
| MVP-08 | Warn before external AI transmission | Live AI requires an explicit provider/data warning confirmation |
| MVP-09 | Enforce file-ingestion production gates | Uploads enabled; SHA-256 + parse; sources missing URL/authority/class/dates/hash/license/SME approval are HOLD and excluded from generation; requirement TXT/CSV/JSON append as draft text |
| MVP-10 | Keep readiness internally consistent | Missing evidence yields `NOT_READY`, score 0, draft document states, and `submission_ready: false` |
| MVP-11 | Keep source mappings precise | FDA CSA is identified as nonbinding, medical-device guidance; GAMP 5 and ISO remain license-gated |
| MVP-12 | Prevent uncontrolled exports from appearing approved | All exports and saved packages are permanently marked `DRAFT_NOT_CONTROLLED` |
| MVP-13 | Validate every supported regulated system | Regression matrix covers LIMS, MES, SCADA/DCS, Serialization, QMS, EDMS, CDS, PV, EDC/eCRF, CTMS, eTMF, Safety Reporting, RIM, ERP/SAP, and Supply Chain |
| MVP-14 | Keep Saved Package controls usable at the larger type size | Label, inputs, Save button, status and note increase by 2px; flex wrapping and shrink-safe inputs keep every control inside the bordered container |
| MVP-15 | Align first-time guidance with the assurance workflow | Versioned guide is re-enabled once for existing users, sits directly above the assurance hero, shares its content boundaries, and the Regulatory Library uses a wider responsive panel |
| MVP-16 | Global regulation comparison for consulting co-operations | **Global Compare** tab renders a citation matrix across US/EU/**UK MHRA**/ICH/**PIC/S**/HIPAA/GDPR (Healthcare & Life Sciences domains and listed system types), pairwise **Differences** column, gap and briefing modes with uncovered-market flags, JSON/CSV export, and optional push to Assure |
| MVP-17 | SOP and policy mapper | **Readiness** tab maps regulations to library selections, client delta / audit gap / ingested SOP text; flags true unmapped controls and lexical conflicts |
| MVP-18 | Inspection readiness assistant | **Readiness** tab generates checklist, per-PBI evidence requests, mock inspection Q&A, and downloadable gap / inspection JSON/CSV |
| MVP-19 | Library and outcome example accessibility | Regulatory Library uses **one** scrollbar for the full library (tree is not a nested scroller). A 20px gap sits between that scrollbar and the resize handle so they do not read as overlapping slivers at 80–100% zoom. Every **Define the business compliance outcome** example is selectable from the dropdown and Try chips |
| MVP-20 | Multi-select regulatory framework and jurisdiction | **Regulatory Framework** and **Jurisdiction** are closed multi-select dropdowns (zero/one/many). Selected frameworks union library sources; selected markets union QC `allowedNations`. Graph: `Frameworks → union library → Jurisdictions → QC nation filter → PBI (DRAFT_NOT_CONTROLLED)`. Verified in `p0-regression.mjs` and `qc-compat-regression.mjs` |
| MVP-21 | Live AI harness token optimization (DeepSeek / low-cost) | CRS harness: compact context line (`buildHarnessContextLine`), scoped `rankChunks` sources for decomposition only, per-agent `max_tokens` and prev-output limits via `LIVE_HARNESS_CONFIG` / `getLiveHarnessProfile`; `callLLM` uses `MODELS[].url` + `MODELS[].model`. Graph: `Scope → Intake → Govern → Decompose → QC → Evidence`. Verified in `p0-regression.mjs` |
| MVP-22 | CTD / eCTD Engine tab | **CTD/eCTD Engine** tab stores in-house documents (SHA-256, session-persisted), validates Module 3.2.S coverage against regulatory corpus scoped by **Regulatory Framework** and **Jurisdiction** filters, exports `DRAFT_NOT_CONTROLLED` mapping JSON/CSV. Platform API: `POST /api/v1/documents`, `POST /api/v1/ctd-engine/validate`, web route `/ctd`. Verified in `p0-regression.mjs` |

## Stakeholder demo script

1. Open `index.html` and click **Quick demo**.
2. Show the automatically scoped FDA/LIMS/Pharma context.
3. Generate the draft and review the readiness banner.
4. Open a source link from a PBI.
5. Enter reviewer identity and a comment, expand acceptance criteria, and record a draft review attestation.
6. Export Jira CSV or JSON and show the `DRAFT_NOT_CONTROLLED` watermark.

## Deployment

The deliverable remains a static single-file application. Replace the existing GitHub Pages `index.html` with the MVP file, review it in a non-production branch, and publish only after the source owner confirms the official links and permitted-use statements.
