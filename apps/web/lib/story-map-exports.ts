import type { StoryMap, StoryMapExport } from "@/lib/story-map-types";
import { STORY_MAP_DISCLAIMER } from "@/lib/story-map-types";

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function csvEscape(value: string | null | undefined): string {
  const text = value ?? "";
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function exportStoryMapJson(exportData: StoryMapExport) {
  const payload = {
    ...exportData,
    exported_at: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  downloadBlob(`DRAFT-story-map-${exportData.story_map.map_key}.json`, blob);
}

export function exportStoryMapCsv(storyMap: StoryMap) {
  const header = [
    "map_key",
    "story_id",
    "title",
    "status",
    "owner",
    "outcome_or_obligation",
    "acceptance_criteria",
    "evidence_required",
    "risk",
    "dependency",
    "source_control_ref",
    "group_key",
    "backbone_id",
    "release_slice_id",
    "trace_link_count",
    "package_status",
  ];
  const lines = [header.join(",")];
  for (const story of storyMap.stories) {
    lines.push(
      [
        storyMap.map_key,
        String(story.id),
        story.title,
        story.status,
        story.owner,
        story.outcome_or_obligation,
        story.acceptance_criteria,
        story.evidence_required,
        story.risk,
        story.dependency,
        story.source_control_ref,
        story.group_key,
        story.backbone_id ? String(story.backbone_id) : "",
        story.release_slice_id ? String(story.release_slice_id) : "",
        String(story.trace_links.length),
        storyMap.package_status,
      ]
        .map(csvEscape)
        .join(","),
    );
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  downloadBlob(`DRAFT-story-map-${storyMap.map_key}.csv`, blob);
}

export function exportStoryMapPng(storyMap: StoryMap, viewLabel: string) {
  const canvas = document.createElement("canvas");
  const width = 1400;
  const lineHeight = 22;
  const padding = 40;
  const storyBlocks = storyMap.stories.map(
    (story) =>
      `• [${story.status}] ${story.title}` +
      (story.owner ? ` — ${story.owner}` : "") +
      (story.trace_links.length ? ` (${story.trace_links.length} links)` : ""),
  );
  const lines = [
    "MARAS Story Map — DRAFT_NOT_CONTROLLED",
    STORY_MAP_DISCLAIMER,
    "",
    `Map: ${storyMap.title} (${storyMap.map_key})`,
    `Template: ${storyMap.template} | View: ${viewLabel}`,
    `Intent: ${storyMap.intent || "(not set)"}`,
    "",
    "Backbones:",
    ...(storyMap.backbones.length
      ? storyMap.backbones.map((b) => `  - ${b.title}`)
      : ["  (none)"]),
    "",
    "Stories:",
    ...(storyBlocks.length ? storyBlocks : ["  (none)"]),
  ];

  const height = padding * 2 + lines.length * lineHeight + 60;
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#92400e";
  ctx.fillRect(0, 0, width, 36);
  ctx.fillStyle = "#fffbeb";
  ctx.font = "bold 14px system-ui, sans-serif";
  ctx.fillText("DRAFT — NOT FOR REGULATORY SUBMISSION", padding, 24);

  ctx.fillStyle = "#111827";
  ctx.font = "14px system-ui, sans-serif";
  let y = padding + 20;
  for (const line of lines) {
    ctx.fillText(line.slice(0, 120), padding, y);
    y += lineHeight;
  }

  canvas.toBlob((blob) => {
    if (!blob) return;
    downloadBlob(`DRAFT-story-map-${storyMap.map_key}.png`, blob);
  });
}

export function exportStoryMapPdf() {
  window.print();
}
