import Link from "next/link";

import { EvidenceReviewer } from "@/components/evidence-reviewer";
import { SiteShell } from "@/components/site-shell";
import { fetchEvidenceReviewContext } from "@/lib/evidence-types";

type EvidenceReviewPageProps = {
  params: Promise<{ id: string }>;
};

export default async function EvidenceReviewPage({ params }: EvidenceReviewPageProps) {
  const { id } = await params;
  const context = await fetchEvidenceReviewContext(id);

  return (
    <SiteShell
      title="Evidence review"
      description="Side-by-side source verification and human review. Approved excerpts are immutable; changes create a new version."
      wide
    >
      {context ? (
        <EvidenceReviewer context={context} />
      ) : (
        <div className="panel text-sm text-muted-foreground">
          Evidence not found.{" "}
          <Link href="/ctd" className="text-primary hover:underline">
            Return to CTD Engine
          </Link>
        </div>
      )}
    </SiteShell>
  );
}
