import { NextRequest } from "next/server";

type RouteContext = { params: Promise<{ path?: string[] }> };

async function forward(request: NextRequest, context: RouteContext) {
  const { path = [] } = await context.params;
  const apiBase =
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  const isReview = path.at(-1) === "review";
  const key = isReview
    ? process.env.MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY
    : process.env.MARAS_REQUIREMENTS_MAPPING_WRITE_KEY;

  if (!key) {
    return Response.json(
      { detail: "Configure the server-side requirements mapping API keys in the web environment." },
      { status: 503 },
    );
  }

  const target = new URL(
    `/api/v1/requirements-mappings${path.length ? `/${path.map(encodeURIComponent).join("/")}` : ""}`,
    apiBase,
  );
  target.search = request.nextUrl.search;

  const headers = new Headers({
    Authorization: `Bearer ${key}`,
  });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  try {
    const upstream = await fetch(target, init);
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { detail: "Requirements mapping API is unreachable. Check API_URL and service status." },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return forward(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return forward(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return forward(request, context);
}
