"""Pytest fixtures for API tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import (  # noqa: F401
    AuditEvent,
    CtdSection,
    Document,
    DocumentPage,
    DocumentParagraph,
    DossierExport,
    EvidenceItem,
    RequirementsMapping,
)
from app.services.ctd_seed import seed_ctd_module_32s


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    seed_ctd_module_32s(session)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    monkeypatch.setenv("MARAS_REQUIREMENTS_MAPPING_WRITE_KEY", "writer-test-key")
    monkeypatch.setenv("MARAS_REQUIREMENTS_MAPPING_REVIEW_KEY", "reviewer-test-key")
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"Authorization": "Bearer writer-test-key"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
