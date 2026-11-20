import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const apiBase = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const key = process.env.MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY ?? process.env.MARAS_REQUIREMENTS_MAPPING_WRITE_KEY;
  if (!key) return Response.json({ detail: "Configure the server-side MARAS reader key." }, { status: 503 });
  try {
    const documentId = request.nextUrl.searchParams.get("document_id");
    if (!documentId || !/^\d+$/.test(documentId)) {
      return Response.json({ detail: "A valid document_id is required." }, { status: 400 });
    }
    const upstreamUrl = new URL(`/api/v1/regulatory-intelligence/graph/${documentId}`, apiBase);
    const upstream = await fetch(upstreamUrl, {
      headers: { Authorization: `Bearer ${key}` },
      cache: "no-store",
    });
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") ?? "application/json", "cache-control": "no-store" },
    });
  } catch {
    return Response.json({ detail: "Regulatory Intelligence API is unreachable." }, { status: 502 });
  }
}
