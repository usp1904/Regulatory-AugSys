import { RegulatoryIntelligenceWorkbench } from "@/components/regulatory-intelligence-workbench";
import { SiteShell } from "@/components/site-shell";

export default function RegulatoryIntelligencePage() {
  return (
    <SiteShell
      title="Regulatory Intelligence"
      description="Retrieve traceable source passages from existing MARAS regulatory documents. This is the first integration slice; semantic retrieval, graph reasoning and grounded generation are planned phases."
      wide
    >
      <RegulatoryIntelligenceWorkbench />
    </SiteShell>
  );
}
