"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addBackbone,
  addReleaseSlice,
  addTraceLink,
  createStory,
  createStoryMap,
  deleteStory,
  deleteTraceLink,
  fetchLinkableSources,
  fetchStoryMap,
  fetchStoryMapExport,
  fetchStoryMaps,
  reorderStories,
  storiesFromMarasImport,
  updateStory,
  updateStoryMap,
  type MarasImportPayload,
  type Story,
  type StoryMap,
} from "@/lib/story-map-api";
import {
  exportStoryMapCsv,
  exportStoryMapJson,
  exportStoryMapPdf,
  exportStoryMapPng,
} from "@/lib/story-map-exports";
import {
  GROUP_BY_LABELS,
  GROUP_BY_OPTIONS,
  RELEASE_MEANING_LABELS,
  RELEASE_MEANINGS,
  STORY_MAP_DISCLAIMER,
  STORY_MAP_GRAPH,
  STORY_MAP_TEMPLATE_LABELS,
  STORY_MAP_TEMPLATES,
  STORY_STATUSES,
  TRACE_LINK_TYPE_LABELS,
  TRACE_LINK_TYPES,
  TRACE_SOURCE_LABELS,
  type GroupByOption,
  type ReleaseMeaning,
  type StoryMapTemplate,
  type StoryMapView,
  type StoryStatus,
  type TraceLinkType,
  type TraceSourceWorkspace,
} from "@/lib/story-map-types";

const STATUS_COLORS: Record<StoryStatus, string> = {
  planned: "bg-blue-100 text-blue-800",
  deferred: "bg-slate-100 text-slate-700",
  blocked: "bg-red-100 text-red-800",
  completed: "bg-emerald-100 text-emerald-800",
};

const VIEW_LABELS: Record<StoryMapView, string> = {
  workshop: "Workshop story-map",
  release: "Release slice",
  traceability: "Regulatory traceability",
  outcome: "Outcome / OKR",
  migration: "Migration readiness",
};

function emptyStoryDraft(): Partial<Story> {
  return {
    title: "",
    owner: "",
    outcome_or_obligation: "",
    acceptance_criteria: "",
    evidence_required: "",
    risk: "",
    dependency: "",
    source_control_ref: "",
    status: "planned",
    group_key: "",
  };
}

export function StoryMapWorkspace() {
  const [maps, setMaps] = useState<StoryMap[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [storyMap, setStoryMap] = useState<StoryMap | null>(null);
  const [view, setView] = useState<StoryMapView>("workshop");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdBy, setCreatedBy] = useState("story-map.author");
  const [newTitle, setNewTitle] = useState("");
  const [newTemplate, setNewTemplate] = useState<StoryMapTemplate>("regulatory_compliance");
  const [editingStory, setEditingStory] = useState<Story | null>(null);
  const [storyDraft, setStoryDraft] = useState<Partial<Story>>(emptyStoryDraft());
  const [dragStoryId, setDragStoryId] = useState<number | null>(null);
  const [importJson, setImportJson] = useState("");
  const [linkableSources, setLinkableSources] = useState<Awaited<
    ReturnType<typeof fetchLinkableSources>
  > | null>(null);
  const [traceDraft, setTraceDraft] = useState({
    link_type: "regulation_control" as TraceLinkType,
    external_ref: "",
    label: "",
    source_workspace: "assure" as TraceSourceWorkspace,
  });

  const refreshMaps = useCallback(async () => {
    const items = await fetchStoryMaps();
    setMaps(items);
  }, []);

  const loadMap = useCallback(async (id: number) => {
    const data = await fetchStoryMap(id);
    setStoryMap(data);
    setSelectedId(id);
  }, []);

  useEffect(() => {
    void refreshMaps();
    void fetchLinkableSources().then(setLinkableSources);
  }, [refreshMaps]);

  useEffect(() => {
    if (selectedId) void loadMap(selectedId);
  }, [selectedId, loadMap]);

  const groupedStories = useMemo(() => {
    if (!storyMap) return new Map<string, Story[]>();
    const keyFor = (story: Story) => {
      if (storyMap.group_by === "persona") return story.group_key ?? "Unassigned persona";
      if (storyMap.group_by === "process") return story.group_key ?? "Unassigned process";
      if (storyMap.group_by === "feature") return story.group_key ?? "Unassigned feature";
      if (storyMap.group_by === "technical_module") {
        return story.group_key ?? "Unassigned module";
      }
      return story.outcome_or_obligation ?? "Unassigned outcome";
    };
    const groups = new Map<string, Story[]>();
    for (const story of storyMap.stories) {
      const key = keyFor(story);
      const bucket = groups.get(key) ?? [];
      bucket.push(story);
      groups.set(key, bucket);
    }
    return groups;
  }, [storyMap]);

  async function runAction(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateMap() {
    if (!newTitle.trim()) return;
    await runAction(async () => {
      const created = await createStoryMap({
        title: newTitle.trim(),
        template: newTemplate,
        intent: "",
        group_by: "outcome",
        created_by: createdBy,
      });
      setNewTitle("");
      await refreshMaps();
      await loadMap(created.id);
    });
  }

  async function handleAddBackbone() {
    if (!storyMap) return;
    const title = window.prompt("Backbone / capability title:");
    if (!title?.trim()) return;
    await runAction(async () => {
      const updated = await addBackbone(storyMap.id, title.trim(), storyMap.backbones.length);
      setStoryMap(updated);
    });
  }

  async function handleAddReleaseSlice() {
    if (!storyMap) return;
    const name = window.prompt("Release slice name:");
    if (!name?.trim()) return;
    await runAction(async () => {
      const updated = await addReleaseSlice(storyMap.id, {
        name: name.trim(),
        release_meaning: "mvp_value_increment",
        sort_order: storyMap.release_slices.length,
      });
      setStoryMap(updated);
    });
  }

  async function handleAddStory(backboneId?: number | null) {
    if (!storyMap) return;
    await runAction(async () => {
      const created = await createStory(storyMap.id, {
        title: "New user story (draft)",
        backbone_id: backboneId ?? null,
        sort_order: storyMap.stories.length,
        status: "planned",
      });
      setEditingStory(created);
      setStoryDraft(created);
      await loadMap(storyMap.id);
    });
  }

  async function handleSaveStory() {
    if (!editingStory || !storyMap) return;
    await runAction(async () => {
      await updateStory(editingStory.id, storyDraft);
      await loadMap(storyMap.id);
      setEditingStory(null);
      setStoryDraft(emptyStoryDraft());
    });
  }

  async function handleDeleteStory(storyId: number) {
    if (!storyMap || !window.confirm("Delete this story?")) return;
    await runAction(async () => {
      await deleteStory(storyId);
      if (editingStory?.id === storyId) {
        setEditingStory(null);
        setStoryDraft(emptyStoryDraft());
      }
      await loadMap(storyMap.id);
    });
  }

  async function handleReorder(targetStoryId: number) {
    if (!storyMap || dragStoryId === null || dragStoryId === targetStoryId) return;
    const ids = storyMap.stories.map((s) => s.id);
    const from = ids.indexOf(dragStoryId);
    const to = ids.indexOf(targetStoryId);
    if (from < 0 || to < 0) return;
    ids.splice(from, 1);
    ids.splice(to, 0, dragStoryId);
    await runAction(async () => {
      const updated = await reorderStories(storyMap.id, ids);
      setStoryMap(updated);
      setDragStoryId(null);
    });
  }

  async function handleImportMarasJson() {
    if (!storyMap || !importJson.trim()) return;
    await runAction(async () => {
      const payload = JSON.parse(importJson) as MarasImportPayload;
      const imported = storiesFromMarasImport(payload);
      for (const item of imported) {
        const story = await createStory(storyMap.id, {
          title: item.title,
          outcome_or_obligation: item.outcome_or_obligation,
          source_control_ref: item.source_control_ref,
          sort_order: storyMap.stories.length,
          status: "planned",
        });
        for (const link of item.trace_links) {
          await addTraceLink(story.id, link);
        }
      }
      setImportJson("");
      await loadMap(storyMap.id);
    });
  }

  async function handleAddTraceLink() {
    if (!editingStory || !traceDraft.external_ref.trim() || !traceDraft.label.trim()) return;
    await runAction(async () => {
      await addTraceLink(editingStory.id, traceDraft);
      const refreshed = await fetchStoryMap(storyMap!.id);
      setStoryMap(refreshed);
      const updatedStory = refreshed?.stories.find((s) => s.id === editingStory.id);
      if (updatedStory) {
        setEditingStory(updatedStory);
        setStoryDraft(updatedStory);
      }
      setTraceDraft((prev) => ({ ...prev, external_ref: "", label: "" }));
    });
  }

  async function handleDeleteTraceLink(linkId: number) {
    if (!editingStory || !storyMap) return;
    await runAction(async () => {
      await deleteTraceLink(linkId);
      await loadMap(storyMap.id);
      const refreshed = await fetchStoryMap(storyMap.id);
      const updatedStory = refreshed?.stories.find((s) => s.id === editingStory.id);
      if (updatedStory) {
        setEditingStory(updatedStory);
        setStoryDraft(updatedStory);
      }
    });
  }

  async function handleExportJson() {
    if (!storyMap) return;
    const data = await fetchStoryMapExport(storyMap.id);
    if (data) exportStoryMapJson(data);
  }

  function renderStoryCard(story: Story, backboneTitle?: string) {
    return (
      <div
        key={story.id}
        draggable
        onDragStart={() => setDragStoryId(story.id)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={() => void handleReorder(story.id)}
        className="cursor-grab rounded-lg border bg-white p-3 shadow-sm active:cursor-grabbing"
      >
        <div className="flex items-start justify-between gap-2">
          <button
            type="button"
            className="text-left text-sm font-medium text-foreground hover:underline"
            onClick={() => {
              setEditingStory(story);
              setStoryDraft(story);
            }}
          >
            {story.title}
          </button>
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[story.status]}`}>
            {story.status}
          </span>
        </div>
        {story.owner ? (
          <p className="mt-1 text-xs text-muted-foreground">Owner: {story.owner}</p>
        ) : null}
        {backboneTitle ? (
          <p className="mt-1 text-xs text-muted-foreground">Backbone: {backboneTitle}</p>
        ) : null}
        {story.trace_links.length > 0 ? (
          <p className="mt-2 text-xs text-primary">
            {story.trace_links.length} traceability link{story.trace_links.length === 1 ? "" : "s"}
          </p>
        ) : null}
      </div>
    );
  }

  function renderWorkshopView() {
    if (!storyMap) return null;
    const unassigned = storyMap.stories.filter((s) => !s.backbone_id);
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-900">Intent</p>
          <textarea
            className="form-input mt-2 min-h-[72px]"
            value={storyMap.intent}
            onChange={(event) =>
              setStoryMap((prev) => (prev ? { ...prev, intent: event.target.value } : prev))
            }
            onBlur={() => {
              if (!storyMap) return;
              void runAction(async () => {
                await updateStoryMap(storyMap.id, { intent: storyMap.intent });
              });
            }}
            placeholder="Describe the intent for this story map (draft)…"
          />
        </div>

        <div className="overflow-x-auto">
          <div className="flex min-w-max gap-4">
            {storyMap.backbones.map((backbone) => (
              <div key={backbone.id} className="w-72 shrink-0 space-y-3">
                <div className="rounded-md bg-primary/10 px-3 py-2 text-sm font-semibold text-primary">
                  {backbone.title}
                </div>
                {storyMap.stories
                  .filter((s) => s.backbone_id === backbone.id)
                  .map((story) => renderStoryCard(story, backbone.title))}
                <button
                  type="button"
                  className="btn-secondary w-full text-xs"
                  onClick={() => void handleAddStory(backbone.id)}
                  disabled={busy}
                >
                  + Add story
                </button>
              </div>
            ))}
            <div className="w-72 shrink-0 space-y-3">
              <div className="rounded-md bg-muted px-3 py-2 text-sm font-semibold">Unassigned</div>
              {unassigned.map((story) => renderStoryCard(story))}
              <button
                type="button"
                className="btn-secondary w-full text-xs"
                onClick={() => void handleAddStory(null)}
                disabled={busy}
              >
                + Add story
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderReleaseView() {
    if (!storyMap) return null;
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {storyMap.release_slices.map((slice) => (
          <div key={slice.id} className="rounded-lg border bg-card p-4">
            <div className="mb-2">
              <h3 className="font-semibold">{slice.name}</h3>
              <p className="text-xs text-muted-foreground">
                {RELEASE_MEANING_LABELS[slice.release_meaning]}
              </p>
            </div>
            <div className="space-y-2">
              {storyMap.stories
                .filter((s) => s.release_slice_id === slice.id)
                .map((story) => renderStoryCard(story))}
              {storyMap.stories.filter((s) => s.release_slice_id === slice.id).length === 0 ? (
                <p className="text-xs text-muted-foreground">No stories in this slice yet.</p>
              ) : null}
            </div>
          </div>
        ))}
        {storyMap.release_slices.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Add release slices to plan regulatory deadlines, MVP increments, migration waves, or PI
            objectives.
          </p>
        ) : null}
      </div>
    );
  }

  function renderTraceabilityView() {
    if (!storyMap) return null;
    return (
      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full text-sm">
          <thead className="bg-muted/60 text-left">
            <tr>
              <th className="px-3 py-2">Story</th>
              <th className="px-3 py-2">Source / control ref</th>
              <th className="px-3 py-2">Link type</th>
              <th className="px-3 py-2">External ref</th>
              <th className="px-3 py-2">Workspace</th>
            </tr>
          </thead>
          <tbody>
            {storyMap.stories.flatMap((story) =>
              story.trace_links.length > 0
                ? story.trace_links.map((link) => (
                    <tr key={link.id} className="border-t">
                      <td className="px-3 py-2">{story.title}</td>
                      <td className="px-3 py-2">{story.source_control_ref ?? "—"}</td>
                      <td className="px-3 py-2">{TRACE_LINK_TYPE_LABELS[link.link_type]}</td>
                      <td className="px-3 py-2 font-mono text-xs">{link.external_ref}</td>
                      <td className="px-3 py-2">{TRACE_SOURCE_LABELS[link.source_workspace]}</td>
                    </tr>
                  ))
                : [
                    <tr key={story.id} className="border-t text-muted-foreground">
                      <td className="px-3 py-2">{story.title}</td>
                      <td className="px-3 py-2">{story.source_control_ref ?? "—"}</td>
                      <td className="px-3 py-2" colSpan={3}>
                        No traceability links — connect to Assure, SOP Mapper, gaps, compare, or CTD
                        outputs
                      </td>
                    </tr>,
                  ],
            )}
          </tbody>
        </table>
      </div>
    );
  }

  function renderOutcomeView() {
    if (!storyMap) return null;
    return (
      <div className="space-y-4">
        {[...groupedStories.entries()].map(([group, stories]) => (
          <div key={group} className="rounded-lg border p-4">
            <h3 className="mb-3 font-semibold">
              {GROUP_BY_LABELS[storyMap.group_by]}: {group}
            </h3>
            <div className="grid gap-2 md:grid-cols-2">{stories.map((s) => renderStoryCard(s))}</div>
          </div>
        ))}
        {groupedStories.size === 0 ? (
          <p className="text-sm text-muted-foreground">Add stories to group by outcome or OKR.</p>
        ) : null}
      </div>
    );
  }

  function renderMigrationView() {
    if (!storyMap) return null;
    const migrationStories = storyMap.stories.filter(
      (s) =>
        s.status === "blocked" ||
        s.status === "deferred" ||
        (s.dependency?.length ?? 0) > 0 ||
        s.trace_links.some((l) => l.source_workspace === "validation_gaps"),
    );
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Migration readiness highlights blocked/deferred stories, dependencies, and validation gap
          links. Evidence indicates gaps require SME review before migration sign-off.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          {migrationStories.length > 0
            ? migrationStories.map((s) => renderStoryCard(s))
            : null}
        </div>
        {migrationStories.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No migration risks flagged yet. Mark stories as blocked/deferred or link validation gaps.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="story-map-print-root space-y-6">
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
        <p className="font-semibold">{STORY_MAP_DISCLAIMER}</p>
        <p className="mt-1 text-xs">{STORY_MAP_GRAPH}</p>
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4 rounded-lg border bg-card p-4">
          <h2 className="text-sm font-semibold">Story maps</h2>
          <div className="space-y-2">
            {maps.map((map) => (
              <button
                key={map.id}
                type="button"
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  selectedId === map.id ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
                onClick={() => setSelectedId(map.id)}
              >
                <span className="font-medium">{map.title}</span>
                <span className="mt-0.5 block text-xs opacity-80">
                  {STORY_MAP_TEMPLATE_LABELS[map.template]}
                </span>
              </button>
            ))}
          </div>

          <div className="space-y-2 border-t pt-4">
            <label className="form-label">New map title</label>
            <input
              className="form-input"
              value={newTitle}
              onChange={(event) => setNewTitle(event.target.value)}
              placeholder="e.g. Part 11 LIMS migration"
            />
            <label className="form-label">Template</label>
            <select
              className="form-input"
              value={newTemplate}
              onChange={(event) => setNewTemplate(event.target.value as StoryMapTemplate)}
            >
              {STORY_MAP_TEMPLATES.map((template) => (
                <option key={template} value={template}>
                  {STORY_MAP_TEMPLATE_LABELS[template]}
                </option>
              ))}
            </select>
            <label className="form-label">Author</label>
            <input
              className="form-input"
              value={createdBy}
              onChange={(event) => setCreatedBy(event.target.value)}
            />
            <button
              type="button"
              className="btn-primary w-full"
              onClick={() => void handleCreateMap()}
              disabled={busy || !newTitle.trim()}
            >
              Create draft map
            </button>
          </div>
        </aside>

        <section className="space-y-4">
          {!storyMap ? (
            <p className="text-sm text-muted-foreground">
              Select or create a story map to begin workshop planning.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold">{storyMap.title}</h2>
                  <p className="text-xs text-muted-foreground">
                    {storyMap.map_key} · {STORY_MAP_TEMPLATE_LABELS[storyMap.template]} ·{" "}
                    {storyMap.package_status}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className="btn-secondary text-xs" onClick={() => void handleAddBackbone()} disabled={busy}>
                    + Backbone
                  </button>
                  <button type="button" className="btn-secondary text-xs" onClick={() => void handleAddReleaseSlice()} disabled={busy}>
                    + Release slice
                  </button>
                  <button type="button" className="btn-secondary text-xs" onClick={() => void handleExportJson()} disabled={busy}>
                    Export JSON
                  </button>
                  <button
                    type="button"
                    className="btn-secondary text-xs"
                    onClick={() => exportStoryMapCsv(storyMap)}
                    disabled={busy}
                  >
                    Export CSV
                  </button>
                  <button
                    type="button"
                    className="btn-secondary text-xs"
                    onClick={() => exportStoryMapPng(storyMap, VIEW_LABELS[view])}
                    disabled={busy}
                  >
                    Export PNG
                  </button>
                  <button
                    type="button"
                    className="btn-secondary text-xs"
                    onClick={() => exportStoryMapPdf()}
                    disabled={busy}
                  >
                    Export PDF
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <label className="text-sm font-medium">Group by</label>
                <select
                  className="form-input w-auto"
                  value={storyMap.group_by}
                  onChange={(event) => {
                    const group_by = event.target.value as GroupByOption;
                    void runAction(async () => {
                      const updated = await updateStoryMap(storyMap.id, { group_by });
                      setStoryMap(updated);
                    });
                  }}
                >
                  {GROUP_BY_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {GROUP_BY_LABELS[option]}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap gap-1 border-b pb-2">
                {(Object.keys(VIEW_LABELS) as StoryMapView[]).map((viewKey) => (
                  <button
                    key={viewKey}
                    type="button"
                    className={`rounded-md px-3 py-1.5 text-sm ${
                      view === viewKey ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                    }`}
                    onClick={() => setView(viewKey)}
                  >
                    {VIEW_LABELS[viewKey]}
                  </button>
                ))}
              </div>

              <div className="story-map-view-panel">
                {view === "workshop" ? renderWorkshopView() : null}
                {view === "release" ? renderReleaseView() : null}
                {view === "traceability" ? renderTraceabilityView() : null}
                {view === "outcome" ? renderOutcomeView() : null}
                {view === "migration" ? renderMigrationView() : null}
              </div>

              <div className="rounded-lg border bg-muted/30 p-4">
                <h3 className="text-sm font-semibold">Import MARAS outputs (traceability)</h3>
                <p className="mt-1 text-xs text-muted-foreground">
                  Paste JSON exported from Assure, Global Compare, Readiness (SOP mapper / inspection /
                  validation gaps), or CTD/eCTD Engine. Stories are created with draft traceability
                  links — existing workspaces are not modified.
                </p>
                <textarea
                  className="form-input mt-2 min-h-[100px] font-mono text-xs"
                  value={importJson}
                  onChange={(event) => setImportJson(event.target.value)}
                  placeholder='{"schema":"maras.fda.clinical-regulatory-assurance.v1", ...}'
                />
                <button
                  type="button"
                  className="btn-secondary mt-2 text-xs"
                  onClick={() => void handleImportMarasJson()}
                  disabled={busy || !importJson.trim()}
                >
                  Import as draft stories
                </button>
              </div>
            </>
          )}
        </section>
      </div>

      {editingStory ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-card p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Edit story (draft)</h3>
              <button
                type="button"
                className="text-sm text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setEditingStory(null);
                  setStoryDraft(emptyStoryDraft());
                }}
              >
                Close
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {(
                [
                  ["title", "Title"],
                  ["owner", "Owner"],
                  ["group_key", "Group key (persona/process/feature/module)"],
                  ["outcome_or_obligation", "Outcome or regulatory obligation"],
                  ["acceptance_criteria", "Acceptance criteria"],
                  ["evidence_required", "Evidence required"],
                  ["risk", "Risk"],
                  ["dependency", "Dependency"],
                  ["source_control_ref", "Source / control reference"],
                ] as const
              ).map(([field, label]) => (
                <label key={field} className={field.includes("criteria") || field.includes("obligation") ? "sm:col-span-2" : ""}>
                  <span className="form-label">{label}</span>
                  {field === "acceptance_criteria" || field === "outcome_or_obligation" ? (
                    <textarea
                      className="form-input mt-1 min-h-[72px]"
                      value={(storyDraft[field] as string) ?? ""}
                      onChange={(event) =>
                        setStoryDraft((prev) => ({ ...prev, [field]: event.target.value }))
                      }
                    />
                  ) : (
                    <input
                      className="form-input mt-1"
                      value={(storyDraft[field] as string) ?? ""}
                      onChange={(event) =>
                        setStoryDraft((prev) => ({ ...prev, [field]: event.target.value }))
                      }
                    />
                  )}
                </label>
              ))}

              <label>
                <span className="form-label">Status</span>
                <select
                  className="form-input mt-1"
                  value={storyDraft.status ?? "planned"}
                  onChange={(event) =>
                    setStoryDraft((prev) => ({
                      ...prev,
                      status: event.target.value as StoryStatus,
                    }))
                  }
                >
                  {STORY_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span className="form-label">Release slice</span>
                <select
                  className="form-input mt-1"
                  value={storyDraft.release_slice_id ?? ""}
                  onChange={(event) =>
                    setStoryDraft((prev) => ({
                      ...prev,
                      release_slice_id: event.target.value ? Number(event.target.value) : null,
                    }))
                  }
                >
                  <option value="">Unassigned</option>
                  {storyMap?.release_slices.map((slice) => (
                    <option key={slice.id} value={slice.id}>
                      {slice.name} ({RELEASE_MEANING_LABELS[slice.release_meaning]})
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span className="form-label">Backbone</span>
                <select
                  className="form-input mt-1"
                  value={storyDraft.backbone_id ?? ""}
                  onChange={(event) =>
                    setStoryDraft((prev) => ({
                      ...prev,
                      backbone_id: event.target.value ? Number(event.target.value) : null,
                    }))
                  }
                >
                  <option value="">Unassigned</option>
                  {storyMap?.backbones.map((backbone) => (
                    <option key={backbone.id} value={backbone.id}>
                      {backbone.title}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-6 space-y-3 border-t pt-4">
              <h4 className="text-sm font-semibold">Traceability links</h4>
              {editingStory.trace_links.map((link) => (
                <div
                  key={link.id}
                  className="flex items-center justify-between rounded border px-3 py-2 text-xs"
                >
                  <span>
                    [{TRACE_SOURCE_LABELS[link.source_workspace]}] {link.label} — {link.external_ref}
                  </span>
                  <button
                    type="button"
                    className="text-red-600 hover:underline"
                    onClick={() => void handleDeleteTraceLink(link.id)}
                  >
                    Remove
                  </button>
                </div>
              ))}

              <div className="grid gap-2 sm:grid-cols-2">
                <select
                  className="form-input"
                  value={traceDraft.link_type}
                  onChange={(event) =>
                    setTraceDraft((prev) => ({
                      ...prev,
                      link_type: event.target.value as TraceLinkType,
                    }))
                  }
                >
                  {TRACE_LINK_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {TRACE_LINK_TYPE_LABELS[type]}
                    </option>
                  ))}
                </select>
                <select
                  className="form-input"
                  value={traceDraft.source_workspace}
                  onChange={(event) =>
                    setTraceDraft((prev) => ({
                      ...prev,
                      source_workspace: event.target.value as TraceSourceWorkspace,
                    }))
                  }
                >
                  {Object.entries(TRACE_SOURCE_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
                <input
                  className="form-input sm:col-span-2"
                  placeholder="External reference (control ID, CTD code, PBI ID…)"
                  value={traceDraft.external_ref}
                  onChange={(event) =>
                    setTraceDraft((prev) => ({ ...prev, external_ref: event.target.value }))
                  }
                />
                <input
                  className="form-input sm:col-span-2"
                  placeholder="Link label"
                  value={traceDraft.label}
                  onChange={(event) =>
                    setTraceDraft((prev) => ({ ...prev, label: event.target.value }))
                  }
                />
              </div>

              {linkableSources ? (
                <div className="flex flex-wrap gap-2 text-xs">
                  {linkableSources.ctd_sections.slice(0, 5).map((section) => (
                    <button
                      key={section.code}
                      type="button"
                      className="rounded border px-2 py-1 hover:bg-muted"
                      onClick={() =>
                        setTraceDraft({
                          link_type: "ctd_section",
                          external_ref: section.code,
                          label: `CTD ${section.code}: ${section.title}`,
                          source_workspace: "ctd_ectd",
                        })
                      }
                    >
                      CTD {section.code}
                    </button>
                  ))}
                  {linkableSources.evidence_items.slice(0, 3).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="rounded border px-2 py-1 hover:bg-muted"
                      onClick={() =>
                        setTraceDraft({
                          link_type: "pbi_evidence_request",
                          external_ref: item.evidence_key,
                          label: `Evidence ${item.evidence_key}`,
                          source_workspace: "evidence",
                        })
                      }
                    >
                      {item.evidence_key}
                    </button>
                  ))}
                </div>
              ) : null}

              <button
                type="button"
                className="btn-secondary text-xs"
                onClick={() => void handleAddTraceLink()}
                disabled={busy}
              >
                Add traceability link
              </button>
            </div>

            <div className="mt-6 flex justify-between gap-2">
              <button
                type="button"
                className="text-sm text-red-600 hover:underline"
                onClick={() => void handleDeleteStory(editingStory.id)}
              >
                Delete story
              </button>
              <button type="button" className="btn-primary" onClick={() => void handleSaveStory()} disabled={busy}>
                Save draft story
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
