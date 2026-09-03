import type {
  Backbone,
  GroupByOption,
  LinkableSources,
  ReleaseMeaning,
  ReleaseSlice,
  Story,
  StoryMap,
  StoryMapExport,
  StoryMapTemplate,
  StoryStatus,
  TraceLinkType,
  TraceSourceWorkspace,
} from "@/lib/story-map-types";

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string };
    return body.detail ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function fetchStoryMaps(): Promise<StoryMap[]> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps`, { cache: "no-store" });
  if (!res.ok) return [];
  const body = (await res.json()) as { items: StoryMap[] };
  return body.items;
}

export async function fetchStoryMap(id: number): Promise<StoryMap | null> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as StoryMap;
}

export async function fetchStoryMapExport(id: number): Promise<StoryMapExport | null> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${id}/export`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as StoryMapExport;
}

export async function fetchLinkableSources(): Promise<LinkableSources | null> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/linkable-sources`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as LinkableSources;
}

export async function createStoryMap(payload: {
  title: string;
  template: StoryMapTemplate;
  intent?: string;
  group_by?: GroupByOption;
  created_by: string;
}): Promise<StoryMap> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StoryMap;
}

export async function updateStoryMap(
  id: number,
  payload: { title?: string; intent?: string; group_by?: GroupByOption },
): Promise<StoryMap> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StoryMap;
}

export async function addBackbone(mapId: number, title: string, sortOrder: number): Promise<StoryMap> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${mapId}/backbones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, sort_order: sortOrder }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StoryMap;
}

export async function addReleaseSlice(
  mapId: number,
  payload: { name: string; release_meaning: ReleaseMeaning; description?: string; sort_order: number },
): Promise<StoryMap> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${mapId}/release-slices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StoryMap;
}

export async function createStory(
  mapId: number,
  payload: Partial<Story> & { title: string },
): Promise<Story> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${mapId}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as Story;
}

export async function updateStory(
  storyId: number,
  payload: Partial<Story>,
): Promise<Story> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/stories/${storyId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as Story;
}

export async function reorderStories(mapId: number, storyIds: number[]): Promise<StoryMap> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/${mapId}/stories/reorder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ story_ids: storyIds }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StoryMap;
}

export async function deleteStory(storyId: number): Promise<void> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/stories/${storyId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function addTraceLink(
  storyId: number,
  payload: {
    link_type: TraceLinkType;
    external_ref: string;
    label: string;
    source_workspace: TraceSourceWorkspace;
  },
): Promise<void> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/stories/${storyId}/trace-links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function deleteTraceLink(linkId: number): Promise<void> {
  const res = await fetch(`${apiBase()}/api/v1/story-maps/trace-links/${linkId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export type MarasImportPayload = {
  schema?: string;
  schemaId?: string;
  schemaVersion?: string;
  packageStatus?: string;
  controls?: Array<{ id?: string; reg?: string; title?: string }>;
  pbis?: Array<{ id?: string; title?: string; story?: string; regRef?: string }>;
  stories?: Array<{ id?: string; title?: string; story?: string; regRef?: string }>;
  mappings?: Array<{ regulation?: string; sopRef?: string; gap?: string }>;
  inspectionReadiness?: { blockingGaps?: string[] };
  validationGaps?: Array<{ id?: string; label?: string }>;
  differences?: Array<{ topic?: string; market?: string; summary?: string }>;
  mappings_ctd?: Array<{ ctdSection?: string; sectionTitle?: string }>;
};

export function inferSourceWorkspace(payload: MarasImportPayload): TraceSourceWorkspace {
  const schema = payload.schema ?? payload.schemaId ?? payload.schemaVersion ?? "";
  if (schema.includes("global-regulation-compare")) return "global_compare";
  if (schema.includes("inspection-readiness")) return "inspection_readiness";
  if (schema.includes("readiness-gaps")) return "validation_gaps";
  if (schema.includes("ctd-mapping")) return "ctd_ectd";
  if (schema.includes("clinical-regulatory-assurance")) return "assure";
  return "assure";
}

export function storiesFromMarasImport(payload: MarasImportPayload): Array<{
  title: string;
  outcome_or_obligation: string | null;
  source_control_ref: string | null;
  trace_links: Array<{
    link_type: TraceLinkType;
    external_ref: string;
    label: string;
    source_workspace: TraceSourceWorkspace;
  }>;
}> {
  const source = inferSourceWorkspace(payload);
  const results: Array<{
    title: string;
    outcome_or_obligation: string | null;
    source_control_ref: string | null;
    trace_links: Array<{
      link_type: TraceLinkType;
      external_ref: string;
      label: string;
      source_workspace: TraceSourceWorkspace;
    }>;
  }> = [];

  const pbis = payload.pbis ?? payload.stories ?? [];
  for (const pbi of pbis) {
    results.push({
      title: pbi.title ?? pbi.story ?? "Imported PBI",
      outcome_or_obligation: pbi.story ?? null,
      source_control_ref: pbi.regRef ?? null,
      trace_links: [
        {
          link_type: "pbi_evidence_request",
          external_ref: pbi.id ?? pbi.title ?? "pbi",
          label: `Assure PBI: ${pbi.title ?? pbi.id}`,
          source_workspace: source,
        },
      ],
    });
  }

  for (const gap of payload.inspectionReadiness?.blockingGaps ?? []) {
    results.push({
      title: `Inspection gap: ${gap}`,
      outcome_or_obligation: gap,
      source_control_ref: null,
      trace_links: [
        {
          link_type: "gap_inspection_item",
          external_ref: gap,
          label: `Inspection item: ${gap}`,
          source_workspace: "inspection_readiness",
        },
      ],
    });
  }

  for (const diff of payload.differences ?? []) {
    results.push({
      title: `Compare diff: ${diff.topic ?? diff.market ?? "topic"}`,
      outcome_or_obligation: diff.summary ?? null,
      source_control_ref: diff.market ?? null,
      trace_links: [
        {
          link_type: "comparison_difference",
          external_ref: `${diff.topic ?? ""}:${diff.market ?? ""}`,
          label: `Global Compare: ${diff.topic ?? diff.market}`,
          source_workspace: "global_compare",
        },
      ],
    });
  }

  for (const mapping of payload.mappings ?? []) {
    if (!mapping.gap && !mapping.sopRef) continue;
    results.push({
      title: mapping.gap ?? `SOP map: ${mapping.regulation}`,
      outcome_or_obligation: mapping.regulation ?? null,
      source_control_ref: mapping.sopRef ?? null,
      trace_links: [
        {
          link_type: mapping.gap ? "gap_inspection_item" : "sop_policy",
          external_ref: mapping.sopRef ?? mapping.regulation ?? "sop",
          label: mapping.gap ? `SOP gap: ${mapping.gap}` : `SOP: ${mapping.sopRef}`,
          source_workspace: "sop_mapper",
        },
      ],
    });
  }

  for (const ctd of payload.mappings_ctd ?? []) {
    results.push({
      title: ctd.sectionTitle ?? `CTD ${ctd.ctdSection}`,
      outcome_or_obligation: ctd.sectionTitle ?? null,
      source_control_ref: ctd.ctdSection ?? null,
      trace_links: [
        {
          link_type: "ctd_section",
          external_ref: ctd.ctdSection ?? "ctd",
          label: `CTD ${ctd.ctdSection}`,
          source_workspace: "ctd_ectd",
        },
      ],
    });
  }

  return results;
}

export type { Backbone, ReleaseSlice, Story, StoryMap, StoryStatus };
