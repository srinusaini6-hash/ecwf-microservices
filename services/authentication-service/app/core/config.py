from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ECWF Authentication Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    debug: bool = False
    log_level: str = "INFO"

    database_url: str
    internal_api_key: str
    enable_external_services: bool = True
    http_timeout_seconds: float = 15.0
    http_connect_timeout_seconds: float = 5.0

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "ecwf-authentication-service"
    jwt_audience: str = "ecwf-services"
    max_concurrent_sessions: int = 3
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    otp_token_expire_minutes: int = 5
    otp_max_retries: int = 5
    otp_max_resends: int = 3

    registration_otp_cookie_name: str = "registration_otp_token"
    password_reset_otp_cookie_name: str = "password_reset_otp_token"
    password_reset_verified_cookie_name: str = "password_reset_verified_token"
    mfa_otp_cookie_name: str = "mfa_otp_token"
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    cookie_path: str = "/"
    cors_origins: str = "http://localhost:8001,http://localhost:8002,http://localhost:8003,http://localhost:8004"

    user_service_url: str = "http://user-service:8002"
    tenant_admin_service_url: str = "http://tenant-admin-service:8003"
    notification_service_url: str = "http://notification-service:8004"

    oauth_state_expire_minutes: int = 10
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8001/auth/google/callback"
    google_authorization_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_userinfo_url: str = "https://openidconnect.googleapis.com/v1/userinfo"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def otp_expire_minutes(self) -> int:
        return self.otp_token_expire_minutes

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
