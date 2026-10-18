"use client";

import { useCallback, useEffect, useState } from "react";

type MappingOption = { id: number; mapping_key: string; dossier_id: string; data: { obligation?: string; pbi?: Record<string, unknown> } };
type HistoryItem = { id: number; action: string; actor: string; snapshot: Record<string, unknown>; created_at: string | null };
type Question = { id: number; question_key: string; mapping_id: number; mapping_key: string; dossier_id: string; question: string; owner: string; created_by: string; status: string; answer: string | null; answered_by: string | null; decision: string | null; rationale: string | null; due_date: string | null; resolved_by: string | null; history: HistoryItem[] };
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ClarificationQueue() {
  const [mappings, setMappings] = useState<MappingOption[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [mappingId, setMappingId] = useState("");
  const [questionText, setQuestionText] = useState("");
  const [owner, setOwner] = useState("system.owner");
  const [createdBy, setCreatedBy] = useState("regulatory.author");
  const [dueDate, setDueDate] = useState("");
  const [actor, setActor] = useState("stakeholder");
  const [answer, setAnswer] = useState("");
  const [decision, setDecision] = useState("");
  const [rationale, setRationale] = useState("");
  const [newOwner, setNewOwner] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    const [mappingResponse, questionResponse] = await Promise.all([
      fetch("/api/mapping"),
      fetch("/api/mapping/clarifications"),
    ]);
    if (!mappingResponse.ok || !questionResponse.ok) throw new Error("Could not load mappings or clarification queue.");
    setMappings((await mappingResponse.json()) as MappingOption[]);
    setQuestions((await questionResponse.json()) as Question[]);
  }, []);

  useEffect(() => {
    void refresh().catch((e: unknown) => setError(e instanceof Error ? e.message : "Queue load failed."));
  }, [refresh]);

  const visible = statusFilter === "ALL" ? questions : questions.filter((q) => q.status === statusFilter);
  const current = questions.find((q) => q.id === selected) ?? null;

  async function createQuestion() {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/mapping/clarifications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mapping_id: Number(mappingId), question: questionText, owner, created_by: createdBy, due_date: dueDate || null }),
      });
      const body = (await response.json()) as Question & { detail?: string };
      if (!response.ok) throw new Error(body.detail || "Could not create question.");
      setQuestionText(""); setDueDate(""); setSelected(body.id);
      await refresh();
      setNotice("Created " + body.question_key + ". The linked mapping is now blocked pending a decision.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not create question."); }
    finally { setBusy(false); }
  }

  async function act(action: "ANSWER" | "CONFIRM" | "REJECT" | "REOPEN" | "ASSIGN") {
    if (!current) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/mapping/clarifications/" + current.id, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actor, action, answer: answer || null, decision: decision || null, rationale: rationale || null, owner: newOwner || null }),
      });
      const body = (await response.json()) as Question & { detail?: string };
      if (!response.ok) throw new Error(body.detail || "Could not update question.");
      await refresh();
      setSelected(body.id); setAnswer(""); setDecision(""); setRationale(""); setNotice(body.question_key + " updated: " + body.status);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not update question."); }
    finally { setBusy(false); }
  }

  return <div className="space-y-6">
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.3fr]">
      <section className="panel space-y-4">
        <div className="flex items-center justify-between"><h2 className="font-semibold">Clarification queue</h2><button type="button" className="btn-secondary" onClick={() => void refresh()}>Refresh</button></div>
        <label className="block space-y-1.5"><span className="form-label">Filter status</span><select className="form-input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>{["ALL","OPEN","ANSWERED","CONFIRMED","REJECTED","REOPENED"].map(s => <option key={s} value={s}>{s}</option>)}</select></label>
        {visible.length === 0 ? <p className="text-sm text-muted-foreground">No clarification questions match this filter.</p> : <div className="space-y-2">{visible.map(q => <button key={q.id} type="button" onClick={() => { setSelected(q.id); setAnswer(""); setDecision(""); setRationale(""); }} className={"w-full rounded-lg border p-3 text-left "+(selected===q.id?"border-primary bg-muted":"")}><span className="block text-xs font-semibold text-primary">{q.question_key} · {q.status}</span><span className="mt-1 block text-sm">{q.question}</span><span className="mt-1 block text-xs text-muted-foreground">{q.mapping_key} · Owner: {q.owner}{q.due_date ? " · Due "+q.due_date : ""}</span></button>)}</div>}
      </section>
      <div className="space-y-6">
        <section className="panel space-y-4">
          <h2 className="font-semibold">Raise a clarification</h2>
          <label className="block space-y-1.5"><span className="form-label">Linked mapping</span><select className="form-input" value={mappingId} onChange={e=>setMappingId(e.target.value)}><option value="">Select mapping…</option>{mappings.map(m=><option key={m.id} value={m.id}>{m.mapping_key} · {m.dossier_id} · {String(m.data.pbi?.title || m.data.obligation || "Draft")}</option>)}</select></label>
          <label className="block space-y-1.5"><span className="form-label">Question for System Owner / SME</span><textarea className="form-input" rows={3} value={questionText} onChange={e=>setQuestionText(e.target.value)} placeholder="State the exact ambiguity or evidence needed."/></label>
          <div className="grid gap-3 sm:grid-cols-2"><label className="space-y-1.5"><span className="form-label">Question owner</span><input className="form-input" value={owner} onChange={e=>setOwner(e.target.value)}/></label><label className="space-y-1.5"><span className="form-label">Raised by</span><input className="form-input" value={createdBy} onChange={e=>setCreatedBy(e.target.value)}/></label><label className="space-y-1.5"><span className="form-label">Due date (optional)</span><input type="date" className="form-input" value={dueDate} onChange={e=>setDueDate(e.target.value)}/></label></div>
          <button className="btn-primary" type="button" disabled={busy||!mappingId||questionText.trim().length<8||!owner.trim()||!createdBy.trim()} onClick={()=>void createQuestion()}>Create clarification</button>
        </section>
        {current ? <section className="panel space-y-4">
          <div><h2 className="font-semibold">{current.question_key} · {current.status}</h2><p className="mt-1 text-sm text-muted-foreground">Mapping: {current.mapping_key} · Owner: {current.owner}</p><p className="mt-3 text-sm">{current.question}</p></div>
          {current.answer ? <div className="rounded-lg border p-3 text-sm"><span className="font-medium">Answer by {current.answered_by}:</span><p className="mt-1">{current.answer}</p></div> : null}
          {current.decision ? <div className="rounded-lg border p-3 text-sm"><span className="font-medium">Decision:</span><p className="mt-1">{current.decision}</p><p className="mt-2 text-muted-foreground">{current.rationale}</p></div> : null}
          <label className="block space-y-1.5"><span className="form-label">Acting stakeholder</span><input className="form-input" value={actor} onChange={e=>setActor(e.target.value)}/></label>
          <div className="flex flex-wrap items-end gap-2"><label className="min-w-48 flex-1 space-y-1.5"><span className="form-label">Reassign owner</span><input className="form-input" value={newOwner} onChange={e=>setNewOwner(e.target.value)} placeholder="new.owner"/></label><button className="btn-secondary" type="button" disabled={busy||!newOwner.trim()} onClick={()=>void act("ASSIGN")}>Assign</button></div>
          {current.status === "OPEN" || current.status === "REOPENED" ? <><label className="block space-y-1.5"><span className="form-label">Answer</span><textarea className="form-input" rows={3} value={answer} onChange={e=>setAnswer(e.target.value)}/></label><button className="btn-primary" type="button" disabled={busy||answer.trim().length<4} onClick={()=>void act("ANSWER")}>Record answer</button></> : null}
          {current.status === "ANSWERED" ? <><label className="block space-y-1.5"><span className="form-label">Decision</span><textarea className="form-input" rows={2} value={decision} onChange={e=>setDecision(e.target.value)} placeholder="Confirm the interpretation or reject it."/></label><label className="block space-y-1.5"><span className="form-label">Decision rationale</span><textarea className="form-input" rows={2} value={rationale} onChange={e=>setRationale(e.target.value)}/></label><div className="flex flex-wrap gap-2"><button className="btn-primary" type="button" disabled={busy||decision.trim().length<4||rationale.trim().length<8} onClick={()=>void act("CONFIRM")}>Confirm decision</button><button className="btn-secondary" type="button" disabled={busy||rationale.trim().length<8} onClick={()=>void act("REJECT")}>Reject interpretation</button></div></> : null}
          {current.status === "CONFIRMED" || current.status === "REJECTED" ? <><label className="block space-y-1.5"><span className="form-label">Reason to reopen</span><textarea className="form-input" rows={2} value={rationale} onChange={e=>setRationale(e.target.value)}/></label><button className="btn-secondary" type="button" disabled={busy||rationale.trim().length<8} onClick={()=>void act("REOPEN")}>Reopen question</button></> : null}
          <details className="rounded-lg border p-3"><summary className="cursor-pointer font-medium">Append-only decision history ({current.history.length})</summary><div className="mt-3 space-y-3">{current.history.map(h=><div key={h.id} className="border-l-2 pl-3 text-sm"><p className="font-medium">{h.action} · {h.actor}</p><p className="text-xs text-muted-foreground">{h.created_at || "Timestamp unavailable"}</p><pre className="mt-1 whitespace-pre-wrap break-words text-xs">{JSON.stringify(h.snapshot,null,2)}</pre></div>)}</div></details>
        </section> : null}
      </div>
    </div>
    {error ? <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">{error}</p> : null}
    {notice ? <p role="status" className="rounded-md border border-primary/20 bg-primary/5 px-4 py-3 text-sm">{notice}</p> : null}
  </div>;
}
