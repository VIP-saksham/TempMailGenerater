from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "tempmail-vps"
    app_env: str = "production"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./app.db"

    mail_domain: str = "mail.yourdomain.com"
    mail_ttl_hours: int = 24
    cleanup_interval_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
