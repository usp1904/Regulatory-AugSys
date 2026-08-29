import Link from "next/link";

import { EvidenceReviewer } from "@/components/evidence-reviewer";
import { fetchEvidenceReviewContext } from "@/lib/evidence-types";

type EvidenceReviewPageProps = {
  params: Promise<{ id: string }>;
};

export default async function EvidenceReviewPage({ params }: EvidenceReviewPageProps) {
  const { id } = await params;
  const context = await fetchEvidenceReviewContext(id);

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Evidence review</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Side-by-side source verification and human review. Approved excerpts are immutable; changes
          create a new version. Draft internal record only — not submission-validated.
        </p>
      </div>

      {context ? (
        <EvidenceReviewer context={context} />
      ) : (
        <div className="rounded-md border p-4 text-sm text-muted-foreground">
          Evidence not found.{" "}
          <Link href="/ctd" className="text-primary hover:underline">
            Return to CTD/eCTD Engine
          </Link>
        </div>
      )}
    </main>
  );
}
