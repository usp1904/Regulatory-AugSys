import { RegulatoryIntelligenceWorkbench } from "@/components/regulatory-intelligence-workbench";
import { SiteShell } from "@/components/site-shell";

export default function RegulatoryIntelligencePage() {
  return (
    <SiteShell
      title="Regulatory Intelligence"
      description="Search current MARAS source documents, inspect traceable evidence, and review the retrieval execution path. Index documents here before exploring their candidate provenance graph."
      wide
    >
      <RegulatoryIntelligenceWorkbench />
    </SiteShell>
  );
}
