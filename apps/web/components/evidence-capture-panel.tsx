"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EVIDENCE_TYPES } from "@/lib/evidence-types";

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type EvidenceCapturePanelProps = {
  documentId: number;
  documentVersion: number;
  pageNumber: number | null;
  initialExcerpt?: string;
};

export function EvidenceCapturePanel({
  documentId,
  documentVersion,
  pageNumber,
  initialExcerpt = "",
}: EvidenceCapturePanelProps) {
  const router = useRouter();
  const [dossierId, setDossierId] = useState("");
  const [ctdSectionCode, setCtdSectionCode] = useState("");
  const [excerpt, setExcerpt] = useState(initialExcerpt);
  const [summary, setSummary] = useState("");
  const [evidenceType, setEvidenceType] = useState<string>("DIRECT_EVIDENCE");
  const [createdBy, setCreatedBy] = useState("cmc.author");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (initialExcerpt) setExcerpt(initialExcerpt);
  }, [initialExcerpt]);

  async function capture() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/evidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dossier_id: dossierId,
          ctd_section_code: ctdSectionCode || null,
          source_document_id: documentId,
          page_number: pageNumber,
          exact_source_excerpt: excerpt,
          normalized_summary: summary || null,
          evidence_type: evidenceType,
          created_by: createdBy,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Capture failed");
        return;
      }
      router.push(`/evidence/review/${body.id}`);
    } catch {
      setError("Network error while capturing evidence.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-md border p-4">
      <h2 className="mb-3 text-sm font-medium">Capture evidence</h2>
      <p className="mb-4 text-xs text-muted-foreground">
        Select text in the extracted content panel, then complete this form. Source document version{" "}
        {documentVersion} will be recorded automatically.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium">Dossier ID</span>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            value={dossierId}
            onChange={(e) => setDossierId(e.target.value)}
            placeholder="DOS-2026-001"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">CTD section</span>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            value={ctdSectionCode}
            onChange={(e) => setCtdSectionCode(e.target.value)}
            placeholder="3.2.S.7.3"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">Evidence type</span>
          <select
            className="mt-1 w-full rounded border px-3 py-2"
            value={evidenceType}
            onChange={(e) => setEvidenceType(e.target.value)}
          >
            {EVIDENCE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium">Exact source excerpt</span>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2 font-mono text-sm"
            rows={3}
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium">Normalized summary (optional)</span>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            rows={2}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium">Created by</span>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            value={createdBy}
            onChange={(e) => setCreatedBy(e.target.value)}
          />
        </label>
      </div>
      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
      <button
        type="button"
        className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        disabled={busy || !dossierId.trim() || !excerpt.trim()}
        onClick={capture}
      >
        Capture and open review
      </button>
    </div>
  );
}
