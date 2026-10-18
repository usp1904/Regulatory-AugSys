"use client";

import { useCallback, useEffect, useState } from "react";

type Doc = { id: number; filename: string; version: number; parse_status: string; file_hash: string; text_excerpt: string | null };
type Candidate = { id: number; obligation_key: string; source_document_id: number; source_version: number; source_file_hash: string; clause_id: string; segment_index: number; excerpt: string; trigger_terms: string; extraction_method: string; confidence: number; status: string; reviewer: string | null; review_rationale: string | null; mapping_id?: number | null };
type Mapping = { id: number; mapping_key: string };
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ObligationWorkbench() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [requestedBy, setRequestedBy] = useState("regulatory.author");
  const [reviewer, setReviewer] = useState("regulatory.sme");
  const [rationale, setRationale] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refreshDocs = useCallback(async () => {
    const response = await fetch(api + "/api/v1/documents");
    if (!response.ok) throw new Error("Could not load controlled documents.");
    const body = (await response.json()) as { documents: Doc[] };
    setDocs(body.documents);
    if (!documentId && body.documents.length) setDocumentId(String(body.documents[0].id));
  }, [documentId]);

  const refreshCandidates = useCallback(async () => {
    if (!documentId) { setCandidates([]); return; }
    const response = await fetch("/api/mapping/obligations?document_id=" + encodeURIComponent(documentId));
    if (!response.ok) throw new Error("Could not load obligation candidates.");
    setCandidates((await response.json()) as Candidate[]);
  }, [documentId]);

  useEffect(() => {
    void refreshDocs().catch((e: unknown) => setError(e instanceof Error ? e.message : "Document load failed."));
  }, [refreshDocs]);
  useEffect(() => {
    void refreshCandidates().catch((e: unknown) => setError(e instanceof Error ? e.message : "Candidate load failed."));
  }, [refreshCandidates]);

  const selectedDoc = docs.find((doc) => doc.id === Number(documentId));
  const visible = filter === "ALL" ? candidates : candidates.filter((item) => item.status === filter);

  async function extract() {
    if (!documentId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/mapping/obligations/extract/" + documentId, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requested_by: requestedBy }),
      });
      const body = (await response.json()) as Candidate[] & { detail?: string };
      if (!response.ok) throw new Error((body as unknown as { detail?: string }).detail || "Extraction failed.");
      await refreshCandidates();
      setNotice("Extraction completed. " + body.length + " candidate(s) found or reused. Review each candidate before creating a mapping.");
    } catch (e) { setError(e instanceof Error ? e.message : "Extraction failed."); }
    finally { setBusy(false); }
  }

  async function review(item: Candidate, decision: "APPROVED" | "REJECTED") {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/mapping/obligations/" + item.id + "/review", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer, decision, rationale }),
      });
      const body = (await response.json()) as Candidate & { detail?: string };
      if (!response.ok) throw new Error(body.detail || "Candidate review failed.");
      await refreshCandidates();
      setRationale("");
      setNotice(body.obligation_key + " marked " + body.status + ".");
    } catch (e) { setError(e instanceof Error ? e.message : "Candidate review failed."); }
    finally { setBusy(false); }
  }

  async function createMapping(item: Candidate) {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/mapping/obligations/" + item.id + "/create-mapping?created_by=" + encodeURIComponent(requestedBy), { method: "POST" });
      const body = (await response.json()) as Mapping & { detail?: string };
      if (!response.ok) throw new Error(body.detail || "Could not create mapping draft.");
      await refreshCandidates();
      setNotice("Created draft " + body.mapping_key + ". Open Requirements Mapping to add authority URL, system evidence, decisions, requirement, PBI, and tests.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not create mapping draft."); }
    finally { setBusy(false); }
  }

  return <div className="space-y-6">
    <section className="panel space-y-4">
      <div><h2 className="text-lg font-semibold">Extract obligation candidates</h2><p className="mt-1 text-sm text-muted-foreground">Rule-based screening of extracted text. It identifies sentences containing normative terms; it does not interpret law or establish compliance.</p></div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-1.5"><span className="form-label">Controlled source document</span><select className="form-input" value={documentId} onChange={e=>setDocumentId(e.target.value)}><option value="">Select document…</option>{docs.map(doc=><option key={doc.id} value={doc.id}>{doc.filename} · v{doc.version} · {doc.parse_status}</option>)}</select></label>
        <label className="space-y-1.5"><span className="form-label">Requested by</span><input className="form-input" value={requestedBy} onChange={e=>setRequestedBy(e.target.value)}/></label>
      </div>
      {selectedDoc ? <div className="rounded-lg border p-3 text-xs text-muted-foreground"><p>Document version: v{selectedDoc.version} · Parse state: {selectedDoc.parse_status}</p><p className="mt-1 break-all">SHA-256: {selectedDoc.file_hash}</p></div> : null}
      <div className="flex flex-wrap gap-3"><button className="btn-primary" type="button" disabled={busy||!documentId||!requestedBy.trim()||selectedDoc?.parse_status!=="EXTRACTED"} onClick={()=>void extract()}>{busy?"Working…":"Extract obligation candidates"}</button><button className="btn-secondary" type="button" disabled={busy} onClick={()=>void refreshCandidates()}>Refresh candidates</button></div>
      {selectedDoc && selectedDoc.parse_status !== "EXTRACTED" ? <p className="text-sm text-amber-800">This document is not ready for extraction. Resolve the parser/hold state first.</p> : null}
    </section>

    <section className="panel space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Candidate register</h2><p className="text-xs text-muted-foreground">Approve only after a subject-matter expert checks the source excerpt and applicability context.</p></div><select className="form-input max-w-48" value={filter} onChange={e=>setFilter(e.target.value)}>{["ALL","DRAFT","APPROVED","REJECTED"].map(s=><option key={s} value={s}>{s}</option>)}</select></div>
      <label className="block max-w-xl space-y-1.5"><span className="form-label">Reviewer / SME</span><input className="form-input" value={reviewer} onChange={e=>setReviewer(e.target.value)}/></label>
      <label className="block space-y-1.5"><span className="form-label">Review rationale</span><textarea className="form-input" rows={2} value={rationale} onChange={e=>setRationale(e.target.value)} placeholder="Required for approval or rejection."/></label>
      {visible.length===0 ? <p className="text-sm text-muted-foreground">No candidates for this document/filter. Run extraction to create draft candidates.</p> : <div className="space-y-4">{visible.map(item=><article key={item.id} className="rounded-xl border p-4 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-xs font-semibold text-primary">{item.obligation_key} · {item.clause_id}</p><p className="mt-1 text-xs text-muted-foreground">Source v{item.source_version} · {item.extraction_method} · heuristic confidence {Math.round(item.confidence*100)}%</p></div><span className="rounded-full border px-2 py-1 text-xs">{item.status}</span></div>
        <blockquote className="border-l-2 pl-3 text-sm">{item.excerpt}</blockquote>
        <p className="text-xs text-muted-foreground">Trigger terms: {item.trigger_terms}</p>
        <p className="break-all text-xs text-muted-foreground">Source SHA-256: {item.source_file_hash}</p>
        {item.reviewer ? <p className="text-xs text-muted-foreground">Reviewed by {item.reviewer}: {item.review_rationale}</p> : null}
        {item.status==="DRAFT" ? <div className="flex flex-wrap gap-2"><button className="btn-primary" type="button" disabled={busy||rationale.trim().length<8||!reviewer.trim()} onClick={()=>void review(item,"APPROVED")}>Approve candidate</button><button className="btn-secondary" type="button" disabled={busy||rationale.trim().length<8||!reviewer.trim()} onClick={()=>void review(item,"REJECTED")}>Reject candidate</button></div> : null}
        {item.status==="APPROVED" && !item.mapping_id ? <button className="btn-primary" type="button" disabled={busy} onClick={()=>void createMapping(item)}>Create traceable mapping draft</button> : null}
        {item.mapping_id ? <p className="text-sm">Mapping created: <a className="underline" href="/requirements-mappings">open Requirements Mapping workbench</a> (record #{item.mapping_id}).</p> : null}
      </article>)}</div>}
    </section>
    {error ? <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">{error}</p> : null}
    {notice ? <p role="status" className="rounded-md border border-primary/20 bg-primary/5 px-4 py-3 text-sm">{notice}</p> : null}
  </div>;
}
