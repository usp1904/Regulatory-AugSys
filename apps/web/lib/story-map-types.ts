export const STORY_MAP_TEMPLATES = [
  "regulatory_compliance",
  "business_process",
  "outcome_oriented",
  "classic_user_journey",
  "feature_breakdown",
  "role_based",
  "component_technical_module",
  "customer_value_stream",
  "legacy_preservation",
  "enterprise_migration",
  "pi_planning",
] as const;

export const STORY_MAP_TEMPLATE_LABELS: Record<StoryMapTemplate, string> = {
  regulatory_compliance: "Regulatory/Compliance",
  business_process: "Business Process",
  outcome_oriented: "Outcome-Oriented",
  classic_user_journey: "Classic User Journey",
  feature_breakdown: "Feature Breakdown",
  role_based: "Role-Based",
  component_technical_module: "Component/Technical Module",
  customer_value_stream: "Customer Value Stream",
  legacy_preservation: "Legacy Preservation",
  enterprise_migration: "Enterprise Migration",
  pi_planning: "PI Planning",
};

export const RELEASE_MEANINGS = [
  "regulatory_deadline",
  "mvp_value_increment",
  "moscow_priority",
  "migration_wave",
  "technical_dependency",
  "pi_objective",
  "outcome_increment",
] as const;

export const RELEASE_MEANING_LABELS: Record<ReleaseMeaning, string> = {
  regulatory_deadline: "Regulatory deadline",
  mvp_value_increment: "MVP/value increment",
  moscow_priority: "MoSCoW priority",
  migration_wave: "Migration wave",
  technical_dependency: "Technical dependency",
  pi_objective: "PI objective",
  outcome_increment: "Outcome increment",
};

export const STORY_STATUSES = ["planned", "deferred", "blocked", "completed"] as const;

export const GROUP_BY_OPTIONS = [
  "persona",
  "process",
  "outcome",
  "feature",
  "technical_module",
] as const;

export const GROUP_BY_LABELS: Record<GroupByOption, string> = {
  persona: "Persona",
  process: "Process",
  outcome: "Outcome",
  feature: "Feature",
  technical_module: "Technical module",
};

export const TRACE_LINK_TYPES = [
  "regulation_control",
  "sop_policy",
  "gap_inspection_item",
  "comparison_difference",
  "ctd_section",
  "pbi_evidence_request",
] as const;

export const TRACE_LINK_TYPE_LABELS: Record<TraceLinkType, string> = {
  regulation_control: "Regulation / control",
  sop_policy: "SOP or policy",
  gap_inspection_item: "Gap or inspection item",
  comparison_difference: "Comparison difference",
  ctd_section: "CTD/eCTD section",
  pbi_evidence_request: "PBI or evidence request",
};

export const TRACE_SOURCE_WORKSPACES = [
  "assure",
  "sop_mapper",
  "inspection_readiness",
  "validation_gaps",
  "global_compare",
  "ctd_ectd",
  "evidence",
] as const;

export const TRACE_SOURCE_LABELS: Record<TraceSourceWorkspace, string> = {
  assure: "Assure",
  sop_mapper: "SOP Mapper",
  inspection_readiness: "Inspection Readiness",
  validation_gaps: "Validation Gaps",
  global_compare: "Global Compare",
  ctd_ectd: "CTD/eCTD",
  evidence: "Evidence",
};

export type StoryMapTemplate = (typeof STORY_MAP_TEMPLATES)[number];
export type ReleaseMeaning = (typeof RELEASE_MEANINGS)[number];
export type StoryStatus = (typeof STORY_STATUSES)[number];
export type GroupByOption = (typeof GROUP_BY_OPTIONS)[number];
export type TraceLinkType = (typeof TRACE_LINK_TYPES)[number];
export type TraceSourceWorkspace = (typeof TRACE_SOURCE_WORKSPACES)[number];
export type StoryMapView =
  | "workshop"
  | "release"
  | "traceability"
  | "outcome"
  | "migration";

export type TraceLink = {
  id: number;
  link_type: TraceLinkType;
  external_ref: string;
  label: string;
  source_workspace: TraceSourceWorkspace;
  created_at: string;
};

export type Backbone = {
  id: number;
  title: string;
  sort_order: number;
};

export type ReleaseSlice = {
  id: number;
  name: string;
  release_meaning: ReleaseMeaning;
  description: string | null;
  sort_order: number;
};

export type Story = {
  id: number;
  title: string;
  backbone_id: number | null;
  release_slice_id: number | null;
  sort_order: number;
  group_key: string | null;
  owner: string | null;
  outcome_or_obligation: string | null;
  acceptance_criteria: string | null;
  evidence_required: string | null;
  risk: string | null;
  dependency: string | null;
  source_control_ref: string | null;
  status: StoryStatus;
  trace_links: TraceLink[];
  created_at: string;
  updated_at: string;
};

export type StoryMap = {
  id: number;
  map_key: string;
  title: string;
  template: StoryMapTemplate;
  intent: string;
  group_by: GroupByOption;
  package_status: string;
  created_by: string;
  backbones: Backbone[];
  release_slices: ReleaseSlice[];
  stories: Story[];
  created_at: string;
  updated_at: string;
};

export type StoryMapExport = {
  schema_version: string;
  package_status: string;
  disclaimer: string;
  story_map: StoryMap;
};

export type LinkableCtdSection = {
  code: string;
  title: string;
  module: string | null;
};

export type LinkableEvidenceItem = {
  id: number;
  evidence_key: string;
  dossier_id: string;
  ctd_section_code: string | null;
  review_status: string;
  evidence_type: string;
};

export type LinkableSources = {
  ctd_sections: LinkableCtdSection[];
  evidence_items: LinkableEvidenceItem[];
};

export const STORY_MAP_DISCLAIMER =
  "DRAFT — SME/QA review required. Not submission-ready evidence or final regulatory interpretation.";

export const STORY_MAP_GRAPH =
  "Intent → Backbone → Capability/Goal → User Story → Acceptance Evidence (DRAFT_NOT_CONTROLLED)";
