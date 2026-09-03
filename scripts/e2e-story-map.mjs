#!/usr/bin/env node
/**
 * E2E smoke test for Story Map workspace API.
 * Usage: node scripts/e2e-story-map.mjs [API_BASE]
 */
const API = process.argv[2] ?? "http://localhost:8000";

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

async function json(method, path, body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new Error(`${method} ${path} -> ${res.status}: ${text}`);
  return data;
}

async function main() {
  console.log("Story Map E2E — API:", API);

  const health = await json("GET", "/health");
  assert(health.status === "ok", "API health not ok");
  console.log("✓ API health");

  const sources = await json("GET", "/api/v1/story-maps/linkable-sources");
  assert(Array.isArray(sources.ctd_sections), "missing ctd_sections");
  console.log(`✓ Linkable sources (${sources.ctd_sections.length} CTD sections)`);

  const created = await json("POST", "/api/v1/story-maps", {
    title: "E2E Part 11 LIMS Story Map",
    template: "regulatory_compliance",
    intent: "Trace controls to release slices for SME review",
    group_by: "outcome",
    created_by: "e2e.tester",
  });
  assert(created.package_status === "DRAFT_NOT_CONTROLLED", "wrong package status");
  const mapId = created.id;
  console.log(`✓ Created story map ${created.map_key}`);

  const withBackbone = await json("POST", `/api/v1/story-maps/${mapId}/backbones`, {
    title: "Audit trail backbone",
    sort_order: 0,
  });
  const backboneId = withBackbone.backbones[0].id;

  const withSlice = await json("POST", `/api/v1/story-maps/${mapId}/release-slices`, {
    name: "MVP Wave 1",
    release_meaning: "mvp_value_increment",
    sort_order: 0,
  });
  const sliceId = withSlice.release_slices[0].id;
  console.log("✓ Backbone and release slice");

  const story = await json("POST", `/api/v1/story-maps/${mapId}/stories`, {
    title: "As QA I need immutable audit trails",
    backbone_id: backboneId,
    release_slice_id: sliceId,
    owner: "qa.reviewer",
    outcome_or_obligation: "21 CFR Part 11 audit trail",
    acceptance_criteria: "Events are attributable",
    status: "planned",
    sort_order: 0,
  });

  await json("POST", `/api/v1/story-maps/stories/${story.id}/trace-links`, {
    link_type: "ctd_section",
    external_ref: sources.ctd_sections[0]?.code ?? "3.2.S",
    label: "CTD section link",
    source_workspace: "ctd_ectd",
  });
  console.log("✓ Story with CTD trace link");

  const exportData = await json("GET", `/api/v1/story-maps/${mapId}/export`);
  assert(exportData.schema_version === "maras.story-map.v1", "bad export schema");
  assert(exportData.disclaimer.includes("SME"), "missing disclaimer");
  console.log("✓ Export JSON with draft disclaimer");

  const webRes = await fetch("http://localhost:3000/story-map");
  assert(webRes.ok, `web /story-map -> ${webRes.status}`);
  const html = await webRes.text();
  assert(html.includes("Story Map Workspace"), "story map page missing title");
  console.log("✓ Web /story-map page loads");

  console.log("\nAll Story Map E2E checks passed.");
}

main().catch((err) => {
  console.error("E2E FAILED:", err.message);
  process.exit(1);
});
