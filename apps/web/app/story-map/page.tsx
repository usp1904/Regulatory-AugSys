import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { StoryMapWorkspace } from "@/components/story-map-workspace";
import { SiteShell } from "@/components/site-shell";
import { STORY_MAP_GRAPH } from "@/lib/story-map-types";

export default function StoryMapPage() {
  return (
    <SiteShell
      title="Story Map Workspace"
      description="Plan and trace user stories across regulatory, migration, and delivery outcomes. All content is draft until SME/QA approval — not submission-ready evidence."
      wide
    >
      <Card>
        <CardHeader>
          <CardTitle>Workshop story mapping</CardTitle>
          <CardDescription>{STORY_MAP_GRAPH}</CardDescription>
        </CardHeader>
        <CardContent>
          <StoryMapWorkspace />
        </CardContent>
      </Card>
    </SiteShell>
  );
}
