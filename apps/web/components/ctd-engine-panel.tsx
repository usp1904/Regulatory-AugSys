"use client";

import { useCallback, useState } from "react";

import { CtdSectionTree } from "@/components/ctd-section-tree";
import { fetchCtdSections, type CtdSectionNode } from "@/lib/ctd-types";

type StoredDocument = {
  id: number;
  filename: string;
  file_hash: string;
  parse_status: string;
  text_excerpt: string | null;
};

type ValidationResult = {
  schemaVersion: string;
  status: string;
  packageStatus: string;
  metrics: {
    supported: number;
    partial: number;
    gapCount: number;
    houseDocCount: number;
  };
  mappings: Array<{
    ctdSection: string;
    sectionTitle: string;
    coverageLevel: string;
    placementRationale: string;
  }>;
};

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function CtdEnginePanel() {
  const [frameworks, setFrameworks] = useState("FDA");
  const [jurisdictions, setJurisdictions] = useState("United States");
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [tree, setTree] = useState<CtdSectionNode[] | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTree = useCallback(async () => {
    const data = await fetchCtdSections();
    setTree(data?.sections ?? null);
  }, []);

  const refreshDocuments = useCallback(async () => {
    const res = await fetch(`${apiBase()}/api/v1/documents`);
    if (!res.ok) return;
    const body = (await res.json()) as { documents: StoredDocument[] };
    setDocuments(body.documents);
  }, []);

  async function handleUpload(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${apiBase()}/api/v1/documents`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      await refreshDocuments();
      await loadTree();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function runValidation() {
    if (!documents.length) {
      setError("Upload at least one in-house document first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/ctd-engine/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_ids: documents.map((d) => d.id),
          frameworks: frameworks.split(",").map((s) => s.trim()).filter(Boolean),
          jurisdictions: jurisdictions.split(",").map((s) => s.trim()).filter(Boolean),
        }),
      });
      if (!res.ok) throw new Error(`Validation failed (${res.status})`);
      setResult((await res.json()) as ValidationResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="font-medium">Regulatory Framework(s)</span>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={frameworks}
            onChange={(e) => setFrameworks(e.target.value)}
            placeholder="FDA, ICH, EU GMP"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Jurisdiction(s)</span>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={jurisdictions}
            onChange={(e) => setJurisdictions(e.target.value)}
            placeholder="United States, European Union"
          />
        </label>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">In-house document upload</label>
        <input
          type="file"
          accept=".txt,.csv,.json"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleUpload(file);
          }}
        />
        {documents.length > 0 ? (
          <ul className="text-sm text-muted-foreground">
            {documents.map((d) => (
              <li key={d.id}>
                {d.filename} — {d.parse_status}
                {d.file_hash ? ` · ${d.file_hash.slice(0, 12)}…` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No documents stored yet.</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          disabled={busy}
          onClick={() => void runValidation()}
        >
          Run validation
        </button>
        <button
          type="button"
          className="rounded-md border px-4 py-2 text-sm disabled:opacity-50"
          disabled={busy}
          onClick={() => {
            void refreshDocuments();
            void loadTree();
          }}
        >
          Refresh
        </button>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {result ? (
        <div className="space-y-3 rounded-md border p-4 text-sm">
          <p>
            <span className="font-medium">Status:</span> {result.status} · {result.packageStatus}
          </p>
          <p>
            Supported: {result.metrics.supported} · Partial: {result.metrics.partial} · Gaps:{" "}
            {result.metrics.gapCount}
          </p>
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {result.mappings.map((m) => (
              <div key={m.ctdSection} className="rounded border p-2">
                <div className="font-mono text-xs text-primary">{m.ctdSection}</div>
                <div className="font-medium">{m.sectionTitle}</div>
                <div className="text-muted-foreground">{m.coverageLevel}</div>
                <div className="text-xs">{m.placementRationale}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {tree && tree.length > 0 ? (
        <div>
          <h3 className="mb-2 text-sm font-medium">CTD taxonomy reference</h3>
          <CtdSectionTree nodes={tree} />
        </div>
      ) : null}
    </div>
  );
}
