import Link from "next/link";

import { DocumentDetailView } from "@/components/document-detail-view";
import { SiteShell } from "@/components/site-shell";
import { fetchDocument } from "@/lib/document-types";

type DocumentPageProps = {
  params: Promise<{ id: string }>;
};

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { id } = await params;
  const document = await fetchDocument(id);

  return (
    <SiteShell
      title="Controlled document"
      description="Immutable source file metadata, extracted text, evidence capture, and audit trail."
      wide
    >
      {document ? (
        <DocumentDetailView document={document} />
      ) : (
        <div className="panel text-sm text-muted-foreground">
          Document not found.{" "}
          <Link href="/ctd" className="text-primary hover:underline">
            Return to CTD Engine
          </Link>
        </div>
      )}
    </SiteShell>
  );
}
