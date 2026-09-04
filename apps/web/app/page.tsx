import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CtdSectionTree } from "@/components/ctd-section-tree";
import { SiteShell } from "@/components/site-shell";
import { fetchCtdSections } from "@/lib/ctd-types";
import Link from "next/link";

type HealthResponse = {
  status: string;
  service: string;
  version: string;
  database: string;
};

async function fetchApiHealth(): Promise<HealthResponse | null> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function HealthPage() {
  const apiHealth = await fetchApiHealth();
  const ctdTree = await fetchCtdSections();

  return (
    <SiteShell
      title="Dashboard"
      description="Internal authoring, evidence capture, and readiness tooling. All outputs are draft suggestions — not approved evidence, not eCTD-validated, not Part 11 compliant."
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Web application</CardTitle>
            <CardDescription>Next.js platform front end</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="font-medium">Status:</span> ok
            </p>
            <p>
              <span className="font-medium">Service:</span> regulatory-augsys-web
            </p>
            <p>
              <span className="font-medium">Version:</span> 0.1.0
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API health</CardTitle>
            <CardDescription>
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/health
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {apiHealth ? (
              <>
                <p>
                  <span className="font-medium">Status:</span> {apiHealth.status}
                </p>
                <p>
                  <span className="font-medium">Service:</span> {apiHealth.service}
                </p>
                <p>
                  <span className="font-medium">Database:</span> {apiHealth.database}
                </p>
              </>
            ) : (
              <p className="text-muted-foreground">
                API unreachable. Start the FastAPI service (see README).
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Platform workflows</CardTitle>
          <CardDescription>End-to-end paths for controlled documents and evidence</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/story-map"
            className="panel block transition-colors hover:border-primary/40 hover:bg-muted/20"
          >
            <h3 className="font-medium">Story Map workspace</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Workshop story maps with release slices, traceability to Assure, CTD, and readiness
              outputs. Draft until SME/QA approval.
            </p>
          </Link>
          <Link
            href="/ctd"
            className="panel block transition-colors hover:border-primary/40 hover:bg-muted/20"
          >
            <h3 className="font-medium">CTD / eCTD Engine</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Upload documents, validate Module 3.2.S coverage, and open source files.
            </p>
          </Link>
          <Link
            href="/dossiers"
            className="panel block transition-colors hover:border-primary/40 hover:bg-muted/20"
          >
            <h3 className="font-medium">Dossier export</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Export approved evidence to PDF, DOCX, or TXT with manifest and watermark.
            </p>
          </Link>
          <div className="panel">
            <h3 className="font-medium">Evidence review</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Capture evidence from a document, then review at{" "}
              <code className="text-xs">/evidence/review/&#123;id&#125;</code>.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CTD Module 3.2.S — Drug Substance</CardTitle>
          <CardDescription>
            Controlled taxonomy for CMC evidence mapping (draft reference; not eCTD-validated).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {ctdTree && ctdTree.sections.length > 0 ? (
            <CtdSectionTree nodes={ctdTree.sections} />
          ) : (
            <p className="text-sm text-muted-foreground">
              CTD sections unavailable. Run migrations and start the API.
            </p>
          )}
        </CardContent>
      </Card>
    </SiteShell>
  );
}
