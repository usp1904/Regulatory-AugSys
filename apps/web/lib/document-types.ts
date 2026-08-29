export type DocumentPage = {
  page_number: number;
  text_content: string;
};

export type DocumentParagraph = {
  paragraph_index: number;
  text_content: string;
};

export type AuditEvent = {
  id: number;
  event_type: string;
  actor: string;
  detail: string | null;
  created_at: string;
};

export type DocumentSummary = {
  id: number;
  filename: string;
  content_type: string;
  byte_size: number;
  file_hash: string;
  version: number;
  uploader: string;
  parse_status: string;
  text_excerpt: string | null;
  extraction_error: string | null;
  created_at: string;
};

export type DocumentDetail = DocumentSummary & {
  pages: DocumentPage[];
  paragraphs: DocumentParagraph[];
  audit_events: AuditEvent[];
};

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchDocument(id: string): Promise<DocumentDetail | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/documents/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as DocumentDetail;
  } catch {
    return null;
  }
}

export function documentDownloadUrl(id: number | string): string {
  return `${apiBase()}/api/v1/documents/${id}/download`;
}
