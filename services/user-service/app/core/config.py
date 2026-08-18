from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ECWF User Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    debug: bool = False
    log_level: str = "INFO"
    database_url: str
    internal_api_key: str
    enable_external_services: bool = True
    http_timeout_seconds: float = 15.0
    http_connect_timeout_seconds: float = 5.0
    auth_service_url: str = "http://authentication-service:8001"
    tenant_admin_service_url: str = "http://tenant-admin-service:8003"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
