from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    ORGANIZATION_SERVICE_URL: str
    NOTIFICATION_SERVICE_URL: str
    INTERNAL_API_KEY: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"


settings = Settings()