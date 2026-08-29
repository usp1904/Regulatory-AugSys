import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CtdEnginePanel } from "@/components/ctd-engine-panel";
import Link from "next/link";

export default function CtdEnginePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">CTD / eCTD Engine</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Store in-house documents and validate Module 3.2.S coverage against regulatory
            references scoped by framework and jurisdiction. Draft suggestions only — not
            eCTD-validated, not submission-ready.
          </p>
        </div>
        <Link href="/" className="text-sm text-primary hover:underline">
          ← Health dashboard
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Module 3.2.S — Drug Substance</CardTitle>
          <CardDescription>
            Upload controlled drafts, select regulatory scope, and run validation via the API.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CtdEnginePanel />
        </CardContent>
      </Card>
    </main>
  );
}
