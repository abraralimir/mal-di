"""Configuration for MAL Document Intelligence backend."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BASE_DIR: Path = Path(__file__).parent.parent
    BACKEND_DIR: Path = Path(__file__).parent
    UPLOADS_DIR: Path = BACKEND_DIR / "uploads"
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    OCR_LANGUAGE: str = "ar,en"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # --- IBM BPM (optional): pooled HTTP client for your REST/exposed document URLs ---
    BPM_BASE_URL: str = ""
    BPM_POOL_CONNECTIONS: int = 10
    BPM_POOL_MAXSIZE: int = 32
    BPM_HTTP_TIMEOUT_SEC: float = 120.0
    BPM_USERNAME: str = ""
    BPM_PASSWORD: str = ""
    BPM_BEARER_TOKEN: str = ""

    # --- FileNet / Content Platform (optional): same pattern, separate pool ---
    FILENET_BASE_URL: str = ""
    FILENET_POOL_CONNECTIONS: int = 10
    FILENET_POOL_MAXSIZE: int = 32
    FILENET_HTTP_TIMEOUT_SEC: float = 120.0
    FILENET_USERNAME: str = ""
    FILENET_PASSWORD: str = ""
    FILENET_BEARER_TOKEN: str = ""


settings = Settings()
