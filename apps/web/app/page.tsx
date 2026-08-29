import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CtdSectionTree } from "@/components/ctd-section-tree";
import { fetchCtdSections } from "@/lib/ctd-types";

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
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Regulatory-AugSys</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Internal authoring, evidence, and readiness tool. Outputs are draft suggestions only —
          not approved evidence, not eCTD-validated, not Part 11 compliant.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Web application</CardTitle>
          <CardDescription>Next.js front end (monorepo skeleton)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
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
            Fetched from {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/health
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          {apiHealth ? (
            <>
              <p>
                <span className="font-medium">Status:</span> {apiHealth.status}
              </p>
              <p>
                <span className="font-medium">Service:</span> {apiHealth.service}
              </p>
              <p>
                <span className="font-medium">Version:</span> {apiHealth.version}
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

      <Card>
        <CardHeader>
          <CardTitle>CTD Module 3.2.S — Drug Substance</CardTitle>
          <CardDescription>
            Controlled taxonomy for CMC evidence mapping (draft reference; not eCTD-validated).
            {" "}
            <a href="/ctd" className="text-primary hover:underline">
              Open CTD/eCTD Engine →
            </a>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {ctdTree && ctdTree.sections.length > 0 ? (
            <CtdSectionTree nodes={ctdTree.sections} />
          ) : (
            <p className="text-sm text-muted-foreground">
              CTD sections unavailable. Run migrations and start the API (
              <code className="text-xs">GET /api/v1/ctd-sections</code>).
            </p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
