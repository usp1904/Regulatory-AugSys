"""Structure-aware extraction for controlled PDF, DOCX and TXT uploads.

PDF text remains page-addressable. Detected tables are serialized into each page's
text stream so the existing MARAS provenance and indexing model can retain them.
Scanned pages use PyMuPDF's optional Tesseract OCR bridge when available.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import pymupdf
from docx import Document as DocxDocument


@dataclass(frozen=True)
class ExtractionResult:
    status: str
    pages: list[str]
    paragraphs: list[str]
    error: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def full_text(self) -> str:
        if self.pages:
            return "\n\n".join(self.pages)
        if self.paragraphs:
            return "\n\n".join(self.paragraphs)
        return ""


def _pdf_page_text(page) -> tuple[str, list[str]]:
    """Extract selectable text and detected tables; OCR only when text is absent."""
    warnings: list[str] = []
    text = page.get_text("text").strip()
    if not text:
        try:
            text_page = page.get_textpage_ocr(language="eng", dpi=200, full=True)
            text = page.get_text("text", textpage=text_page).strip()
            if text:
                warnings.append("OCR_USED")
        except Exception as exc:  # Tesseract is an optional system dependency.
            warnings.append(f"OCR_UNAVAILABLE: {type(exc).__name__}: {exc}")

    table_text: list[str] = []
    try:
        finder = page.find_tables()
        for table_index, table in enumerate(finder.tables, start=1):
            rows = table.extract()
            non_empty_rows = [
                " | ".join(str(cell or "").strip() for cell in row)
                for row in rows
                if any(str(cell or "").strip() for cell in row)
            ]
            if non_empty_rows:
                table_text.append(
                    f"[EXTRACTED TABLE {table_index}]\n" + "\n".join(non_empty_rows)
                )
    except Exception as exc:  # Table detection varies by PDF layout.
        warnings.append(f"PDF_TABLE_DETECTION_WARNING: {type(exc).__name__}")

    if table_text:
        text = "\n\n".join(part for part in (text, *table_text) if part)
    return text, warnings


def extract_pdf_pages(data: bytes) -> ExtractionResult:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            pages: list[str] = []
            warnings: list[str] = []
            for page in pdf:
                page_text, page_warnings = _pdf_page_text(page)
                pages.append(page_text)
                warnings.extend(
                    f"PAGE_{page.number + 1}:{warning}" for warning in page_warnings
                )
        if not pages:
            return ExtractionResult(
                status="EXTRACTION_FAILED",
                pages=[],
                paragraphs=[],
                error="PDF contained no pages",
            )
        if not any(page.strip() for page in pages):
            return ExtractionResult(
                status="OCR_REQUIRED",
                pages=pages,
                paragraphs=[],
                error=(
                    "No selectable text was extracted. OCR was unavailable or returned "
                    "no text. Install and configure Tesseract OCR, then reprocess the source."
                ),
                warnings=tuple(warnings),
            )
        return ExtractionResult(
            status="EXTRACTED", pages=pages, paragraphs=[], warnings=tuple(warnings)
        )
    except Exception as exc:  # noqa: BLE001 — surface extraction failure to caller
        return ExtractionResult(
            status="EXTRACTION_FAILED",
            pages=[],
            paragraphs=[],
            error=str(exc),
        )


def extract_docx_paragraphs(data: bytes) -> ExtractionResult:
    try:
        doc = DocxDocument(io.BytesIO(data))
        paragraphs = [
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        ]
        for table_index, table in enumerate(doc.tables, start=1):
            rows = [
                " | ".join(cell.text.strip().replace("\n", " ") for cell in row.cells)
                for row in table.rows
            ]
            rows = [row for row in rows if row.replace("|", "").strip()]
            if rows:
                paragraphs.append(
                    f"[EXTRACTED TABLE {table_index}]\n" + "\n".join(rows)
                )
        if not paragraphs:
            return ExtractionResult(
                status="EXTRACTION_FAILED",
                pages=[],
                paragraphs=[],
                error="DOCX contained no non-empty paragraphs or tables",
            )
        return ExtractionResult(status="EXTRACTED", pages=[], paragraphs=paragraphs)
    except Exception as exc:  # noqa: BLE001
        return ExtractionResult(
            status="EXTRACTION_FAILED",
            pages=[],
            paragraphs=[],
            error=str(exc),
        )


def extract_txt_pages(data: bytes) -> ExtractionResult:
    try:
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            return ExtractionResult(
                status="EXTRACTION_FAILED",
                pages=[],
                paragraphs=[],
                error="TXT file was empty",
            )
        return ExtractionResult(status="EXTRACTED", pages=[text], paragraphs=[])
    except Exception as exc:  # noqa: BLE001
        return ExtractionResult(
            status="EXTRACTION_FAILED",
            pages=[],
            paragraphs=[],
            error=str(exc),
        )


def extract_document(content_type: str, data: bytes) -> ExtractionResult:
    media_type = content_type.split(";")[0].strip().lower()
    if media_type == "application/pdf":
        return extract_pdf_pages(data)
    if media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_docx_paragraphs(data)
    if media_type == "text/plain":
        return extract_txt_pages(data)
    return ExtractionResult(
        status="UNSUPPORTED_MIME",
        pages=[],
        paragraphs=[],
        error=f"Unsupported media type: {media_type}",
    )
