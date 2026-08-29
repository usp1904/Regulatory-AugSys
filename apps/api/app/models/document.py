"""Controlled in-house document storage metadata."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(128), nullable=False, default="application/octet-stream"
    )
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploader: Mapped[str] = mapped_column(String(256), nullable=False, default="unknown")
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pages: Mapped[list[DocumentPage]] = relationship(
        "DocumentPage",
        back_populates="document",
        order_by="DocumentPage.page_number",
        cascade="all, delete-orphan",
    )
    paragraphs: Mapped[list[DocumentParagraph]] = relationship(
        "DocumentParagraph",
        back_populates="document",
        order_by="DocumentParagraph.paragraph_index",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(
        "AuditEvent",
        back_populates="document",
        order_by="AuditEvent.created_at",
    )

    def full_extracted_text(self) -> str:
        if self.pages:
            return "\n\n".join(page.text_content for page in self.pages)
        if self.paragraphs:
            return "\n\n".join(paragraph.text_content for paragraph in self.paragraphs)
        return self.text_excerpt or ""


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    document: Mapped[Document] = relationship("Document", back_populates="pages")


class DocumentParagraph(Base):
    __tablename__ = "document_paragraphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paragraph_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    document: Mapped[Document] = relationship("Document", back_populates="paragraphs")
