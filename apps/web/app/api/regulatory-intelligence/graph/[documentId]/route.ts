import { NextRequest } from "next/server";

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ documentId: string }> },
) {
  const { documentId } = await context.params;
  if (!/^\d+$/.test(documentId)) {
    return Response.json({ detail: "Invalid document identifier." }, { status: 400 });
  }
  const apiBase = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const key = process.env.MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY ?? process.env.MARAS_REQUIREMENTS_MAPPING_WRITE_KEY;
  if (!key) return Response.json({ detail: "Configure a server-side MARAS reader key." }, { status: 503 });
  try {
    const upstream = await fetch(new URL(`/api/v1/regulatory-intelligence/graph/${documentId}`, apiBase), {
      headers: { Authorization: `Bearer ${key}` },
      cache: "no-store",
    });
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    return Response.json({ detail: "Regulatory Intelligence API is unreachable." }, { status: 502 });
  }
}
