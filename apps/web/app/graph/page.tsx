import { RegulatoryGraphExplorer } from "@/components/regulatory-graph-explorer";
import { SiteShell } from "@/components/site-shell";

export default function RegulatoryGraphPage() {
  return (
    <SiteShell
      title="Graph Exploration"
      description="Explore indexed candidate entities, source-linked co-mentions and the exact evidence passage behind each relationship. Candidate graph edges are not validated regulatory relationships."
      wide
    >
      <RegulatoryGraphExplorer />
    </SiteShell>
  );
}
