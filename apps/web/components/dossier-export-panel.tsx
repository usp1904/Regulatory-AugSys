"use client";

import { useState } from "react";

import type { DossierExportResult, ExportFormat } from "@/lib/dossier-export-types";
import { dossierExportDownloadUrl } from "@/lib/dossier-export-types";

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: "txt", label: "Plain text (.txt)" },
  { value: "docx", label: "Word document (.docx)" },
  { value: "pdf", label: "PDF (.pdf)" },
];

export function DossierExportPanel() {
  const [dossierId, setDossierId] = useState("");
  const [actor, setActor] = useState("export.operator");
  const [format, setFormat] = useState<ExportFormat>("pdf");
  const [result, setResult] = useState<DossierExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function runExport() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/dossiers/${encodeURIComponent(dossierId)}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actor, format }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Export failed");
        return;
      }
      setResult(body as DossierExportResult);
    } catch {
      setError("Unable to reach the API. Ensure the backend is running.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="space-y-2 sm:col-span-2">
          <span className="form-label">Dossier ID</span>
          <input
            className="form-input"
            value={dossierId}
            onChange={(e) => setDossierId(e.target.value)}
            placeholder="DOS-2026-001"
          />
        </label>
        <label className="space-y-2">
          <span className="form-label">Export format</span>
          <select
            className="form-input"
            value={format}
            onChange={(e) => setFormat(e.target.value as ExportFormat)}
          >
            {FORMATS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-2">
          <span className="form-label">Actor</span>
          <input
            className="form-input"
            value={actor}
            onChange={(e) => setActor(e.target.value)}
            placeholder="export.operator"
          />
        </label>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="btn-primary"
          disabled={busy || !dossierId.trim()}
          onClick={() => void runExport()}
        >
          Generate export
        </button>
      </div>

      {error ? (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {result ? (
        <div className="panel space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Export ready
            </span>
            <span className="text-sm text-muted-foreground">
              {result.export_id} · v{result.dossier_version} · {result.manifest.item_count} items
            </span>
          </div>

          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">File hash</dt>
              <dd className="break-all font-mono text-xs">{result.file_hash}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Size</dt>
              <dd>{result.byte_size.toLocaleString()} bytes</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Evidence IDs included</dt>
              <dd>{result.manifest.evidence_ids.join(", ") || "—"}</dd>
            </div>
          </dl>

          <a
            href={dossierExportDownloadUrl(result.export_id)}
            className="btn-primary inline-flex"
            download
          >
            Download {result.export_format.toUpperCase()}
          </a>
        </div>
      ) : null}

      <div className="rounded-lg border border-dashed bg-muted/30 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
        Only <strong className="font-medium text-foreground">APPROVED</strong> evidence is included.
        Gap and confidential-reference items appear in labelled blocks. Every export is watermarked
        and stored immutably with an audit trail.
      </div>
    </div>
  );
}
