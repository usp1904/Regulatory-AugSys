"use client";

import { FormEvent, useState } from "react";

type Evidence = {
  document_id: number;
  filename: string;
  document_version: number;
  file_hash: string;
  location_type: string;
  location: string;
  excerpt: string;
  score: number;
};

type RetrievalResponse = {
  status: string;
  query: string;
  results: Evidence[];
  message: string;
};

export function RegulatoryIntelligenceWorkbench() {
  const [query, setQuery] = useState("");
  const [documentIds, setDocumentIds] = useState("");
  const [result, setResult] = useState<RetrievalResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const parsedIds = documentIds.trim()
      ? documentIds.split(",").map((value) => Number(value.trim())).filter((value) => Number.isInteger(value) && value > 0)
      : undefined;

    try {
      const response = await fetch("/api/regulatory-intelligence/retrieve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          document_ids: parsedIds,
          top_k: 8,
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Evidence retrieval failed.");
      }
      setResult(body as RetrievalResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected retrieval error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-card p-5 shadow-sm">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">Search existing regulatory documents</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Retrieve source passages from MARAS documents already ingested. This initial release
            uses lexical matching and does not generate regulatory advice.
          </p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Regulatory question or search terms</span>
            <textarea
              required
              minLength={3}
              maxLength={2000}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: What audit trail requirements apply to regulated records?"
              className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Optional document IDs</span>
            <input
              value={documentIds}
              onChange={(event) => setDocumentIds(event.target.value)}
              placeholder="For example: 12, 18"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
            <span className="text-xs text-muted-foreground">
              Leave blank to search all extracted documents visible to this MARAS reader.
            </span>
          </label>
          <button
            type="submit"
            disabled={loading || query.trim().length < 3}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Searching sources..." : "Retrieve evidence"}
          </button>
        </form>
        {error ? (
          <p role="alert" className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            {error}
          </p>
        ) : null}
      </section>

      {result ? (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold">Retrieved evidence</h2>
              <p className="text-sm text-muted-foreground">{result.message}</p>
            </div>
            <span className="rounded-full border px-3 py-1 text-xs font-medium">
              {result.results.length} passage(s)
            </span>
          </div>
          {result.results.length ? (
            <div className="space-y-3">
              {result.results.map((item, index) => (
                <article key={`${item.document_id}-${item.location}-${index}`} className="rounded-xl border bg-card p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="font-semibold">{item.filename}</h3>
                      <p className="text-xs text-muted-foreground">
                        Document #{item.document_id} · Version {item.document_version} · {item.location}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      Lexical score: {item.score.toFixed(2)}
                    </span>
                  </div>
                  <blockquote className="mt-3 border-l-2 pl-3 text-sm leading-relaxed">
                    {item.excerpt}
                  </blockquote>
                  <p className="mt-3 break-all font-mono text-[11px] text-muted-foreground">
                    SHA-256: {item.file_hash}
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
              No matching source passages were found. Try a clause number or different terms.
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
