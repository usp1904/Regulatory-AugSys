export type CtdSectionNode = {
  code: string;
  title: string;
  sort_order: number;
  children: CtdSectionNode[];
};

export type CtdSectionTreeResponse = {
  module: string;
  title: string;
  sections: CtdSectionNode[];
};

export async function fetchCtdSections(): Promise<CtdSectionTreeResponse | null> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/v1/ctd-sections`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as CtdSectionTreeResponse;
  } catch {
    return null;
  }
}
