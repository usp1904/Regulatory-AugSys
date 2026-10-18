import { ObligationWorkbench } from "@/components/obligation-workbench";
import { SiteShell } from "@/components/site-shell";

export default function ObligationsPage() {
  return (
    <SiteShell
      title="Obligation Extraction"
      description="Screen extracted regulatory text for candidate obligations, preserve exact source excerpts and hashes, review candidates, and seed traceable mapping drafts."
      wide
    >
      <ObligationWorkbench />
    </SiteShell>
  );
}
