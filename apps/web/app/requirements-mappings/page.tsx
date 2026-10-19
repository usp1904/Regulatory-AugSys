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
          The separate Requirements Mapping Workbench has been deprecated. Continue in the existing
          Value Package tab, where regulatory source truth and organisational interpretation are
          being integrated into the Feature Traceability Matrix.
        </p>
        <p className="text-sm text-muted-foreground">
          Existing backend APIs and stored records are retained for compatibility; this route no
          longer presents a second mapping workbench.
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
