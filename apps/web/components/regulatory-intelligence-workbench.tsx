"use client";

import { FormEvent, useEffect, useState } from "react";

type SourceDocument = {
  document_id: number;
  filename: string;
  version: number;
  file_hash: string;
  parse_status: string;
};
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
  plan?: { intent: string; strategy: string[]; clause_reference?: string | null; max_graph_hops: number; rationale: string };
  trace?: { stage: string; status: string }[];
  generation_status?: string;
};
type IndexResponse = {
  document_id: number;
  document_version: number;
  chunk_count: number;
  entity_count: number;
  edge_count: number;
  vector_count: number;
  graph_persisted: boolean;
  provider_status: string;
};

export function RegulatoryIntelligenceWorkbench() {
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<RetrievalResponse | null>(null);
  const [indexResult, setIndexResult] = useState<IndexResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);

  async function loadDocuments() {
    try {
      const response = await fetch("/api/regulatory-intelligence/documents", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Could not load MARAS documents.");
      setDocuments(body as SourceDocument[]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load documents.");
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function indexSelected() {
    if (!selectedDocument) return;
    setIndexing(true);
    setError("");
    setIndexResult(null);
    try {
      const response = await fetch("/api/regulatory-intelligence/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: Number(selectedDocument) }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Indexing failed.");
      setIndexResult(body as IndexResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Indexing failed.");
    } finally {
      setIndexing(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/api/regulatory-intelligence/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          document_ids: selectedDocument ? [Number(selectedDocument)] : undefined,
          top_k: 8,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Evidence retrieval failed.");
      setResult(body as RetrievalResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected retrieval error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
        <div>
          <h2 className="text-lg font-semibold">Regulatory knowledge engine</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Uses MARAS-controlled documents as its source of truth. Indexing builds stable source
            chunks, BM25 search data and provenance-linked candidate graph facts in a local SQLite index.
            No cloud account or paid API is required for the local retrieval path.
          </p>
        </div>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium">Existing extracted MARAS document</span>
          <select
            value={selectedDocument}
            onChange={(event) => setSelectedDocument(event.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="">All extracted documents</option>
            {documents.map((doc) => (
              <option key={doc.document_id} value={doc.document_id}>
                #{doc.document_id} · {doc.filename} · v{doc.version}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => void loadDocuments()} className="rounded-md border px-3 py-2 text-sm">
            Refresh documents
          </button>
          <button
            type="button"
            disabled={!selectedDocument || indexing}
            onClick={() => void indexSelected()}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {indexing ? "Building index..." : "Build / refresh RAG index"}
          </button>
        </div>
        {indexResult ? (
          <div className="rounded-lg border p-3 text-sm">
            <p className="font-semibold">Index operation completed · {indexResult.provider_status}</p>
            <p className="mt-1 text-muted-foreground">
              {indexResult.chunk_count} chunks · {indexResult.entity_count} entities ·
              {" "}{indexResult.edge_count} candidate edges · {indexResult.vector_count} cloud vectors persisted
            </p>
            <p className="text-xs text-muted-foreground">
              Local graph index: {indexResult.graph_persisted ? "saved" : "not saved"}
            </p>
          </div>
        ) : null}
      </section>

      <section className="rounded-xl border bg-card p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Ask the regulatory knowledge base</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Local retrieval combines BM25 ranking with source-linked graph expansion. Optional cloud
          embeddings can be added later. Every result retains source document, version, hash and location.
        </p>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Regulatory question</span>
            <textarea
              required
              minLength={3}
              maxLength={2000}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Which controls are associated with 21 CFR Part 11 audit trail requirements?"
              className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <button
            type="submit"
            disabled={loading || query.trim().length < 3}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Retrieving evidence..." : "Retrieve grounded evidence"}
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
          <div>
            <h2 className="text-lg font-semibold">Evidence results</h2>
            <p className="text-sm text-muted-foreground">{result.message}</p>
          </div>
          {result.plan ? (
            <div className="rounded-lg border bg-card p-4 text-sm">
              <p className="font-semibold">Query plan · {result.plan.intent}</p>
              <p className="mt-1 text-muted-foreground">{result.plan.rationale}</p>
              <p className="mt-1 text-xs text-muted-foreground">Strategies: {result.plan.strategy.join(" → ")} · Graph hops: {result.plan.max_graph_hops} · Generation: {result.generation_status}</p>
              {result.trace?.length ? <p className="mt-2 text-xs text-muted-foreground">Execution: {result.trace.map((step) => `${step.stage} (${step.status})`).join(" · ")}</p> : null}
            </div>
          ) : null}
          {result.results.length ? result.results.map((item, index) => (
            <article key={`${item.document_id}-${item.location}-${index}`} className="rounded-xl border bg-card p-4">
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <h3 className="font-semibold">{item.filename}</h3>
                  <p className="text-xs text-muted-foreground">
                    Document #{item.document_id} · Version {item.document_version} · {item.location}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground">Fusion score: {item.score.toFixed(5)}</span>
              </div>
              <blockquote className="mt-3 border-l-2 pl-3 text-sm leading-relaxed">{item.excerpt}</blockquote>
              <p className="mt-3 break-all font-mono text-[11px] text-muted-foreground">SHA-256: {item.file_hash}</p>
            </article>
          )) : (
            <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
              No matching source passages found.
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
