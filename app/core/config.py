from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or defaults."""

    PROJECT_NAME: str = "Bulk Certificate Generator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./certificates.db"
    GENERATED_CERTIFICATES_DIR: str = "generated"
    CERTIFICATE_TEMPLATE_PATH: str = "templates/certificate_template.png"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def generated_dir_path(self) -> Path:
        """Returns Path object for generated certificates directory."""
        path = Path(self.GENERATED_CERTIFICATES_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def template_path(self) -> Path:
        """Returns Path object for certificate template."""
        return Path(self.CERTIFICATE_TEMPLATE_PATH)


settings = Settings()
