from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stylewithus:stylewithus_dev@localhost:5432/stylewithus"
    redis_url: str = "redis://localhost:6379/0"
    firebase_service_account_json: str = "{}"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    storage_bucket_url: str = ""
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
