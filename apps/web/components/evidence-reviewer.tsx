"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import {
  EVIDENCE_TYPES,
  REVIEW_DECISIONS,
  type EvidenceReviewContext,
  type ReviewDecision,
} from "@/lib/evidence-types";

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type EvidenceReviewerProps = {
  context: EvidenceReviewContext;
};

function highlightExcerpt(sourceText: string, excerpt: string): React.ReactNode {
  if (!excerpt.trim() || !sourceText) {
    return sourceText || "No source text available.";
  }
  const index = sourceText.indexOf(excerpt);
  if (index === -1) {
    return (
      <>
        {sourceText}
        <div className="mt-4 rounded border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
          Excerpt not found verbatim on this page. Verify wording against the source.
        </div>
      </>
    );
  }
  return (
    <>
      {sourceText.slice(0, index)}
      <mark className="rounded bg-yellow-200 px-0.5">{sourceText.slice(index, index + excerpt.length)}</mark>
      {sourceText.slice(index + excerpt.length)}
    </>
  );
}

function statusBadgeClass(status: string): string {
  switch (status) {
    case "APPROVED":
      return "bg-green-100 text-green-800";
    case "REJECTED":
      return "bg-red-100 text-red-800";
    case "NEEDS_CLARIFICATION":
      return "bg-amber-100 text-amber-800";
    default:
      return "bg-slate-100 text-slate-800";
  }
}

export function EvidenceReviewer({ context }: EvidenceReviewerProps) {
  const router = useRouter();
  const { evidence, source_document: sourceDocument, source_text: sourceText } = context;

  const [ctdSectionCode, setCtdSectionCode] = useState(evidence.ctd_section_code ?? "");
  const [excerpt, setExcerpt] = useState(evidence.exact_source_excerpt);
  const [summary, setSummary] = useState(evidence.normalized_summary ?? "");
  const [evidenceType, setEvidenceType] = useState(evidence.evidence_type);
  const [actor, setActor] = useState(evidence.created_by);
  const [reviewer, setReviewer] = useState(evidence.reviewer ?? "");
  const [decision, setDecision] = useState<ReviewDecision>(
    (evidence.reviewer_decision as ReviewDecision) ?? "APPROVED",
  );
  const [rationale, setRationale] = useState(evidence.reviewer_rationale ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const excerptLocked = evidence.excerpt_locked;
  const canEdit = evidence.review_status !== "APPROVED";

  const sourceMeta = useMemo(() => {
    if (!sourceDocument) return "No linked source document (gap or reference-only).";
    const parts = [
      sourceDocument.filename,
      `v${sourceDocument.version}`,
      evidence.page_number ? `page ${evidence.page_number}` : null,
    ].filter(Boolean);
    return parts.join(" · ");
  }, [sourceDocument, evidence.page_number]);

  async function saveChanges() {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/evidence/${evidence.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          actor,
          ctd_section_code: ctdSectionCode || null,
          exact_source_excerpt: excerpt,
          normalized_summary: summary || null,
          evidence_type: evidenceType,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(body.detail ?? "Update failed");
        return;
      }
      if (body.id !== evidence.id) {
        router.replace(`/evidence/review/${body.id}`);
        router.refresh();
        return;
      }
      setMessage("Evidence updated.");
      router.refresh();
    } catch {
      setMessage("Network error while saving.");
    } finally {
      setBusy(false);
    }
  }

  async function submitReview() {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/evidence/${evidence.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer,
          decision,
          rationale,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(body.detail ?? "Review submission failed");
        return;
      }
      setMessage(`Review recorded: ${body.review_status}`);
      router.refresh();
    } catch {
      setMessage("Network error while submitting review.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadgeClass(evidence.review_status)}`}
        >
          {evidence.review_status}
        </span>
        <span className="text-muted-foreground">
          {evidence.evidence_key} · v{evidence.evidence_version}
        </span>
        {evidence.supersedes_id ? (
          <Link
            href={`/evidence/review/${evidence.supersedes_id}`}
            className="font-medium text-primary hover:underline"
          >
            Supersedes #{evidence.supersedes_id}
          </Link>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel flex flex-col p-0">
          <header className="border-b px-5 py-4">
            <h2 className="text-base font-semibold">Source text</h2>
            <p className="mt-1 text-xs text-muted-foreground">{sourceMeta}</p>
          </header>
          <pre className="max-h-[32rem] flex-1 overflow-auto whitespace-pre-wrap p-5 text-sm leading-relaxed">
            {highlightExcerpt(sourceText, excerpt)}
          </pre>
        </section>

        <section className="panel space-y-5">
          <h2 className="text-base font-semibold">Evidence record</h2>

          <label className="space-y-2">
            <span className="form-label">Dossier ID</span>
            <input className="form-input bg-muted/30" value={evidence.dossier_id} readOnly />
          </label>

          <label className="space-y-2">
            <span className="form-label">CTD section code</span>
            <input
              className="form-input"
              value={ctdSectionCode}
              onChange={(e) => setCtdSectionCode(e.target.value)}
              placeholder="e.g. 3.2.S.7.3"
            />
          </label>

          {sourceDocument ? (
            <p className="text-xs text-muted-foreground">
              Source document: {sourceDocument.filename} (version {sourceDocument.version})
            </p>
          ) : null}

          {evidence.page_number ? (
            <p className="text-xs text-muted-foreground">Page: {evidence.page_number}</p>
          ) : null}

          <label className="space-y-2">
            <span className="form-label">Exact source excerpt</span>
            {excerptLocked ? (
              <p className="text-xs text-amber-700">
                Locked after approval. Editing creates a new evidence version.
              </p>
            ) : null}
            <textarea
              className="form-input font-mono"
              rows={4}
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
              readOnly={excerptLocked}
            />
          </label>

          <label className="space-y-2">
            <span className="form-label">Normalized summary (optional)</span>
            <textarea
              className="form-input"
              rows={3}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Human-authored summary for dossier use"
            />
          </label>

          <label className="space-y-2">
            <span className="form-label">Evidence type</span>
            <select
              className="form-input"
              value={evidenceType}
              onChange={(e) => setEvidenceType(e.target.value as typeof evidenceType)}
            >
              {EVIDENCE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="form-label">Actor (for edits)</span>
            <input className="form-input" value={actor} onChange={(e) => setActor(e.target.value)} />
          </label>

          {(canEdit || excerptLocked) && (
            <button type="button" className="btn-primary" disabled={busy} onClick={saveChanges}>
              Save changes
            </button>
          )}

          <hr />

          <h3 className="text-base font-semibold">Human review</h3>

          <label className="space-y-2">
            <span className="form-label">Reviewer</span>
            <input
              className="form-input"
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              placeholder="qa.reviewer"
            />
          </label>

          <label className="space-y-2">
            <span className="form-label">Decision</span>
            <select
              className="form-input"
              value={decision}
              onChange={(e) => setDecision(e.target.value as ReviewDecision)}
              disabled={evidence.review_status === "APPROVED"}
            >
              {REVIEW_DECISIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="form-label">Rationale</span>
            <textarea
              className="form-input"
              rows={3}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              disabled={evidence.review_status === "APPROVED"}
            />
          </label>

          {evidence.review_status !== "APPROVED" ? (
            <button
              type="button"
              className="btn-secondary border-primary text-primary"
              disabled={busy || !reviewer.trim() || !rationale.trim()}
              onClick={submitReview}
            >
              Submit review
            </button>
          ) : (
            <p className="text-xs text-muted-foreground">
              Reviewed by {evidence.reviewer} on{" "}
              {evidence.reviewed_at ? new Date(evidence.reviewed_at).toLocaleString() : "—"}
            </p>
          )}
        </section>
      </div>

      {message ? (
        <p className="rounded-md border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
          {message}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-4 text-sm">
        {sourceDocument ? (
          <Link href={`/documents/${sourceDocument.id}`} className="font-medium text-primary hover:underline">
            ← Source document
          </Link>
        ) : null}
        <Link href="/dossiers" className="font-medium text-primary hover:underline">
          Dossier export
        </Link>
      </div>
    </div>
  );
}
