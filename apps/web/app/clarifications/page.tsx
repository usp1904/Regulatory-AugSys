import { ClarificationQueue } from "@/components/clarification-queue";
import { SiteShell } from "@/components/site-shell";

export default function ClarificationsPage() {
  return (
    <SiteShell
      title="Clarification Queue"
      description="Route regulatory ambiguities to System Owners and SMEs, capture answers and explicit decisions, and preserve an append-only decision history. Unresolved questions keep the linked mapping blocked."
      wide
    >
      <ClarificationQueue />
    </SiteShell>
  );
}
