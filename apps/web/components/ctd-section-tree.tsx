import type { CtdSectionNode } from "@/lib/ctd-types";

type CtdSectionTreeProps = {
  nodes: CtdSectionNode[];
  depth?: number;
};

export function CtdSectionTree({ nodes, depth = 0 }: CtdSectionTreeProps) {
  return (
    <ul className={depth === 0 ? "space-y-1" : "ml-4 mt-1 space-y-1 border-l border-border pl-3"}>
      {nodes.map((node) => (
        <li key={node.code}>
          <div className="rounded-md px-2 py-1.5 text-sm hover:bg-muted/60">
            <span className="font-mono text-xs text-primary">{node.code}</span>
            <span className="mx-2 text-muted-foreground">—</span>
            <span>{node.title}</span>
          </div>
          {node.children.length > 0 ? (
            <CtdSectionTree nodes={node.children} depth={depth + 1} />
          ) : null}
        </li>
      ))}
    </ul>
  );
}
