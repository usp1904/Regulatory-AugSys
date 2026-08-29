"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { DocumentDetail } from "@/lib/document-types";
import { documentDownloadUrl } from "@/lib/document-types";

type DocumentDetailViewProps = {
  document: DocumentDetail;
};

export function DocumentDetailView({ document }: DocumentDetailViewProps) {
  const isPaged = document.pages.length > 0;
  const isParagraph = document.paragraphs.length > 0;
  const [pageIndex, setPageIndex] = useState(0);
  const [paragraphIndex, setParagraphIndex] = useState(0);

  const currentText = useMemo(() => {
    if (isPaged) return document.pages[pageIndex]?.text_content ?? "";
    if (isParagraph) return document.paragraphs[paragraphIndex]?.text_content ?? "";
    return document.text_excerpt ?? "";
  }, [document, isPaged, isParagraph, pageIndex, paragraphIndex]);

  return (
    <div className="space-y-6">
      <div className="rounded-md border p-4 text-sm">
        <div className="grid gap-2 sm:grid-cols-2">
          <p>
            <span className="font-medium">Filename:</span> {document.filename}
          </p>
          <p>
            <span className="font-medium">Media type:</span> {document.content_type}
          </p>
          <p>
            <span className="font-medium">Size:</span> {document.byte_size.toLocaleString()} bytes
          </p>
          <p>
            <span className="font-medium">Version:</span> {document.version}
          </p>
          <p>
            <span className="font-medium">Uploader:</span> {document.uploader}
          </p>
          <p>
            <span className="font-medium">Uploaded:</span>{" "}
            {new Date(document.created_at).toLocaleString()}
          </p>
          <p className="sm:col-span-2">
            <span className="font-medium">SHA-256:</span>{" "}
            <code className="break-all text-xs">{document.file_hash}</code>
          </p>
          <p>
            <span className="font-medium">Extraction:</span> {document.parse_status}
          </p>
          <p>
            <span className="font-medium">Storage path:</span>{" "}
            <span className="text-muted-foreground">stored immutably on server</span>
          </p>
        </div>
        {document.extraction_error ? (
          <p className="mt-3 text-destructive">{document.extraction_error}</p>
        ) : null}
        <div className="mt-4">
          <a
            href={documentDownloadUrl(document.id)}
            className="inline-flex rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Download original file
          </a>
        </div>
      </div>

      <div className="rounded-md border p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium">Extracted content</h2>
          {isPaged ? (
            <div className="flex items-center gap-2 text-sm">
              <button
                type="button"
                className="rounded border px-2 py-1 disabled:opacity-50"
                disabled={pageIndex === 0}
                onClick={() => setPageIndex((value) => Math.max(0, value - 1))}
              >
                Previous
              </button>
              <span>
                Page {pageIndex + 1} of {document.pages.length}
              </span>
              <button
                type="button"
                className="rounded border px-2 py-1 disabled:opacity-50"
                disabled={pageIndex >= document.pages.length - 1}
                onClick={() =>
                  setPageIndex((value) => Math.min(document.pages.length - 1, value + 1))
                }
              >
                Next
              </button>
            </div>
          ) : null}
          {isParagraph ? (
            <div className="flex items-center gap-2 text-sm">
              <button
                type="button"
                className="rounded border px-2 py-1 disabled:opacity-50"
                disabled={paragraphIndex === 0}
                onClick={() => setParagraphIndex((value) => Math.max(0, value - 1))}
              >
                Previous
              </button>
              <span>
                Paragraph {paragraphIndex + 1} of {document.paragraphs.length}
              </span>
              <button
                type="button"
                className="rounded border px-2 py-1 disabled:opacity-50"
                disabled={paragraphIndex >= document.paragraphs.length - 1}
                onClick={() =>
                  setParagraphIndex((value) =>
                    Math.min(document.paragraphs.length - 1, value + 1),
                  )
                }
              >
                Next
              </button>
            </div>
          ) : null}
        </div>
        <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-4 text-sm">
          {currentText || "No extracted text available."}
        </pre>
      </div>

      <div className="rounded-md border p-4">
        <h2 className="mb-3 text-sm font-medium">Audit events</h2>
        <ul className="space-y-2 text-sm">
          {document.audit_events.map((event) => (
            <li key={event.id} className="rounded border px-3 py-2">
              <div className="font-medium">
                {event.event_type} · {event.actor}
              </div>
              <div className="text-xs text-muted-foreground">
                {new Date(event.created_at).toLocaleString()}
              </div>
              {event.detail ? (
                <pre className="mt-2 overflow-x-auto text-xs">{event.detail}</pre>
              ) : null}
            </li>
          ))}
        </ul>
      </div>

      <Link href="/ctd" className="text-sm text-primary hover:underline">
        ← Back to CTD/eCTD Engine
      </Link>
    </div>
  );
}
