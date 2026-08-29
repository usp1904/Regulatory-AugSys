import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CtdEnginePanel } from "@/components/ctd-engine-panel";
import { SiteShell } from "@/components/site-shell";

export default function CtdEnginePage() {
  return (
    <SiteShell
      title="CTD / eCTD Engine"
      description="Store in-house documents and validate Module 3.2.S coverage against regulatory references scoped by framework and jurisdiction. Draft suggestions only — not eCTD-validated."
      wide
    >
      <Card>
        <CardHeader>
          <CardTitle>Module 3.2.S — Drug Substance</CardTitle>
          <CardDescription>
            Upload controlled drafts, select regulatory scope, run validation, and capture evidence
            from stored documents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CtdEnginePanel />
        </CardContent>
      </Card>
    </SiteShell>
  );
}
