import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DossierExportPanel } from "@/components/dossier-export-panel";
import { SiteShell } from "@/components/site-shell";

export default function DossiersPage() {
  return (
    <SiteShell
      title="Dossier export"
      description="Generate watermarked PDF, DOCX, or TXT exports from approved evidence. Pending and rejected items are never included."
    >
      <Card>
        <CardHeader>
          <CardTitle>Evidence-based export</CardTitle>
          <CardDescription>
            Enter a dossier ID with approved evidence items. The export engine orders CTD sections
            numerically and attaches source provenance for each factual statement.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DossierExportPanel />
        </CardContent>
      </Card>
    </SiteShell>
  );
}
