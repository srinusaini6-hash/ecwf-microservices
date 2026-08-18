from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ECWF Tenant Admin Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8003
    debug: bool = False
    log_level: str = "INFO"
    database_url: str
    internal_api_key: str
    enable_external_services: bool = True
    http_timeout_seconds: float = 15.0
    http_connect_timeout_seconds: float = 5.0
    auth_service_url: str = "http://authentication-service:8001"
    user_service_url: str = "http://user-service:8002"
    notification_service_url: str = "http://notification-service:8004"
    invitation_preview_url: str = "http://localhost:8003/api/v1/organizations/invitations/preview"
    invitation_expire_days: int = 7
    frontend_base_url: str = "http://localhost:3000"
    default_temporary_access_hours: int = 24
    max_temporary_access_days: int = 30
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
