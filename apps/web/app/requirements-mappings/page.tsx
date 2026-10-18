import { SiteShell } from "@/components/site-shell";
import { RequirementsMappingWorkbench } from "@/components/requirements-mapping-workbench";

export default function RequirementsMappingPage() {
  return (
    <SiteShell
      title="Requirements Mapping Workbench"
      description="Trace regulatory source evidence through obligation, applicability, system impact, stakeholder decisions, requirements, PBIs, acceptance criteria, and review gates. All outputs remain drafts until appropriately reviewed."
      wide
    >
      <RequirementsMappingWorkbench />
    </SiteShell>
  );
}
