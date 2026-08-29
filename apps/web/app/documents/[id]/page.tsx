import Link from "next/link";

import { DocumentDetailView } from "@/components/document-detail-view";
import { fetchDocument } from "@/lib/document-types";

type DocumentPageProps = {
  params: Promise<{ id: string }>;
};

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { id } = await params;
  const document = await fetchDocument(id);

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Controlled document</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Immutable source file metadata, extracted text, and audit trail. Draft internal record
          only — not submission-validated.
        </p>
      </div>

      {document ? (
        <DocumentDetailView document={document} />
      ) : (
        <div className="rounded-md border p-4 text-sm text-muted-foreground">
          Document not found.{" "}
          <Link href="/ctd" className="text-primary hover:underline">
            Return to CTD/eCTD Engine
          </Link>
        </div>
      )}
    </main>
  );
}
