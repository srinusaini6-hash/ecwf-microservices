from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ECWF Notification Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8004
    debug: bool = False
    log_level: str = "INFO"
    database_url: str
    internal_api_key: str
    enable_external_services: bool = True
    http_timeout_seconds: float = 15.0
    http_connect_timeout_seconds: float = 5.0
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_from_email: str = ""
    email_from_address: str = ""
    email_from_name: str = "ECWF"
    notification_max_retries: int = 3
    notification_retry_delay_seconds: int = 2
    developer_redirect_email: str = ""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
