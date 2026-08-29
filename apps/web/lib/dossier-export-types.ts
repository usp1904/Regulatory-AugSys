export type ExportFormat = "txt" | "docx" | "pdf";

export type ExportManifest = {
  export_id: string;
  timestamp: string;
  dossier_id: string;
  dossier_version: number;
  generator_version: string;
  evidence_ids: number[];
  evidence_keys: string[];
  document_hashes: Record<string, string>;
  export_format: string;
  item_count: number;
};

export type DossierExportResult = {
  id: number;
  export_id: string;
  dossier_id: string;
  dossier_version: number;
  export_format: ExportFormat;
  file_hash: string;
  byte_size: number;
  content_type: string;
  manifest: ExportManifest;
  created_by: string;
  created_at: string;
  download_url: string;
};

const apiBase = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function dossierExportDownloadUrl(exportId: string): string {
  return `${apiBase()}/api/v1/dossier-exports/${exportId}/download`;
}
