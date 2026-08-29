export const EVIDENCE_TYPES = [
  "DIRECT_EVIDENCE",
  "SUMMARY_EVIDENCE",
  "REFERENCE_ONLY",
  "CONFIDENTIAL_REFERENCE",
  "GAP",
] as const;

export const REVIEW_STATUSES = [
  "PENDING",
  "APPROVED",
  "REJECTED",
  "NEEDS_CLARIFICATION",
] as const;

export const REVIEW_DECISIONS = ["APPROVED", "REJECTED", "NEEDS_CLARIFICATION"] as const;

export type EvidenceType = (typeof EVIDENCE_TYPES)[number];
export type ReviewStatus = (typeof REVIEW_STATUSES)[number];
export type ReviewDecision = (typeof REVIEW_DECISIONS)[number];

export type EvidenceItem = {
  id: number;
  evidence_key: string;
  evidence_version: number;
  dossier_id: string;
  ctd_section_code: string | null;
  source_document_id: number | null;
  source_document_version: number | null;
  page_number: number | null;
  paragraph_index: number | null;
  exact_source_excerpt: string;
  normalized_summary: string | null;
  evidence_type: EvidenceType;
  review_status: ReviewStatus;
  reviewer: string | null;
  reviewer_decision: string | null;
  reviewer_rationale: string | null;
  supersedes_id: number | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  excerpt_locked: boolean;
};

export type EvidenceReviewContext = {
  evidence: EvidenceItem;
  source_document: {
    id: number;
    filename: string;
    version: number;
    file_hash: string;
  } | null;
  source_text: string;
};

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchEvidenceReviewContext(
  id: string,
): Promise<EvidenceReviewContext | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/evidence/${id}/review-context`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as EvidenceReviewContext;
  } catch {
    return null;
  }
}

export async function fetchEvidenceList(dossierId: string): Promise<EvidenceItem[]> {
  try {
    const res = await fetch(
      `${apiBase()}/api/v1/evidence?dossier_id=${encodeURIComponent(dossierId)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return [];
    const body = (await res.json()) as { items: EvidenceItem[] };
    return body.items;
  } catch {
    return [];
  }
}
