"""Runtime configuration — every knob is environment-driven."""

from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _default_env_files() -> tuple[Path, ...]:
    root = _BACKEND_DIR.parent
    return (
        root / "config" / ".env",
        _BACKEND_DIR / ".env.local",
        _BACKEND_DIR / ".env",
    )


class Settings(BaseSettings):
    """Load order: process env → `meridian-stores/config/.env` → backend `.env.local` / `.env`."""

    model_config = SettingsConfigDict(
        env_prefix="MERIDIAN_STORES_",
        env_file=_default_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Primary rename knob (no MERIDIAN_STORES_ prefix). Also accepts MERIDIAN_STORES_PROJECT_NAME.
    project_name: str = Field(
        default="meridian-stores",
        validation_alias=AliasChoices("MERIDIAN_STORES_PROJECT_NAME", "PROJECT_NAME"),
        description="Slug for this deployment; drives defaults unless overridden below.",
    )

    app_name: str = Field(default="meridian-stores", description="FastAPI title; defaults to project_name.")
    service_name: str = Field(
        default="meridian-stores-svc",
        description="Identifies this deployment in JSON; defaults to {project_name}-svc.",
    )

    api_host: str = Field(default="0.0.0.0", description="Bind address for uvicorn.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Bind port for uvicorn.")

    # Comma-separated list, e.g. "http://localhost:5173,http://127.0.0.1:3000"
    cors_origins: str = Field(
        default="http://localhost:5173",
        description="Allowed browser origins (comma-separated). Use * for any origin (no credentials).",
    )

    hello_message: str = Field(
        default="Hello from meridian-stores.",
        description="Payload returned by GET /api/hello; defaults from project_name.",
    )

    @model_validator(mode="after")
    def _derive_identity_from_project(self) -> Self:
        pn = self.project_name
        if "app_name" not in self.model_fields_set:
            self.app_name = pn
        if "service_name" not in self.model_fields_set:
            self.service_name = f"{pn}-svc"
        if "hello_message" not in self.model_fields_set:
            self.hello_message = f"Hello from {pn}."
        return self

    @field_validator("cors_origins")
    @classmethod
    def strip_origins(cls, v: str) -> str:
        return ",".join(part.strip() for part in v.split(",") if part.strip())


settings = Settings()
