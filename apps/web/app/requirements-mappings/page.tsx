import { SiteShell } from "@/components/site-shell";
import Link from "next/link";

export default function DeprecatedRequirementsMappingPage() {
  return (
    <SiteShell
      title="Requirements Mapping Workbench retired"
      description="MARAS uses one traceability experience to avoid duplicate workflows and conflicting records."
    >
      <section className="panel space-y-4">
        <h2 className="font-semibold">Use the Feature Traceability Matrix</h2>
        <p className="text-sm text-muted-foreground">
          The separate Requirements Mapping Workbench is disabled. Continue using the existing
          Value Package tab and Feature Traceability Matrix as the single traceability experience.
        </p>
        <p className="text-sm text-muted-foreground">
          Existing mapping data and backend APIs are retained for compatibility. This page no
          longer exposes a second mapping workflow.
        </p>
        <Link
          href="https://usp1904.github.io/Regulatory-AugSys/"
          className="inline-flex rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          target="_blank"
          rel="noreferrer"
        >
          Open MARAS Value Package
        </Link>
      </section>
    </SiteShell>
  );
}
