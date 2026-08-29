You are implementing a local-first regulatory evidence-management application named Regulatory-AugSys.

The application manages CTD/eCTD CMC evidence. It must support CTD Module 3.2.S Drug Substance sections and map approved source evidence to each section.

Mandatory principles:
1. Never fabricate scientific, manufacturing, impurity, analytical, batch, stability, validation, or regulatory claims.
2. Any generated dossier statement must have at least one approved source-evidence record, including source document version and page number, or it must be an explicitly approved controlled-gap statement.
3. AI outputs are suggestions only. They must never automatically become approved evidence or dossier content.
4. Every uploaded document must have a SHA-256 checksum, immutable version number, upload timestamp, and original file name.
5. Every create/update/review/export action must create an audit event.
6. The system must never claim regulatory submission validity, eCTD validation success, or 21 CFR Part 11 compliance.
7. The system is an internal authoring, evidence, and readiness tool. It must expose gaps and confidentiality constraints clearly.

Tech stack:
- Front end: Next.js, TypeScript, Tailwind CSS, shadcn/ui.
- Back end: FastAPI, Python 3.12, SQLAlchemy 2, Alembic.
- Database: PostgreSQL with SQLite local-dev fallback.
- File storage: local filesystem through a storage abstraction.
- Extraction: PyMuPDF for PDFs, python-docx for DOCX, UTF-8 reader for TXT.
- Export: ReportLab PDF, python-docx DOCX, TXT, CSV, JSON.
- Local runtime: Docker Compose.

Implement in small vertical slices. Before each change:
- inspect the existing files;
- state the files to modify;
- implement only the requested slice;
- add tests;
- run lint/type checks/tests;
- report exact commands run and any unresolved issues.

Start by creating the monorepo skeleton, Docker Compose, FastAPI health endpoint, Next.js health page, PostgreSQL configuration, Alembic setup, and README with exact local run commands.
