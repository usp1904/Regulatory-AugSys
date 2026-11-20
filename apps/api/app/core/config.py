"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Regulatory-AugSys API"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:///./data/regulatory_augsys.db"
    storage_root: str = "./storage"
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://usp1904.github.io"
    rag_enabled: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    firestore_database: str = "(default)"
    rag_collection_prefix: str = "maras_rag"
    rag_embedding_model: str = "text-embedding-005"
    rag_embedding_dimensions: int = 768
    allowed_upload_mime_types: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "text/plain"
    )

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def allowed_mime_set(self) -> set[str]:
        return {
            mime.strip().lower()
            for mime in self.allowed_upload_mime_types.split(",")
            if mime.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
