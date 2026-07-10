from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv
import os
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_file_path, override=True)

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/style_with_us"
    redis_url: str = "redis://localhost:6379/0"
    firebase_service_account_json: str = "{}"
    # Firebase project id — used for verify-only mode when no key file exists.
    firebase_project_id: str = "style-with-us-49180"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    storage_bucket_url: str = ""
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    # Comma-separated emails always granted the admin role on login.
    admin_emails: str = "admin@stylewithus.com"

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # If firebase_service_account_json is a file path, load it
        if self.firebase_service_account_json.startswith("./"):
            firebase_path = BASE_DIR / self.firebase_service_account_json[2:]
            if firebase_path.exists():
                try:
                    # utf-8-sig strips a UTF-8 BOM if the file was saved with one.
                    with open(firebase_path, encoding="utf-8-sig") as f:
                        self.firebase_service_account_json = json.dumps(json.load(f))
                except Exception as e:
                    # Corrupt/unparseable key: don't crash startup. Leave "{}"
                    # so firebase.py falls back to verify-only mode.
                    print(f"[CONFIG] Warning: could not parse {firebase_path}: {e}")
                    self.firebase_service_account_json = "{}"
            else:
                # No key file: reset to "{}" so init falls back to verify-only
                # mode (using firebase_project_id) instead of treating the path
                # string as JSON.
                print(f"[CONFIG] Warning: Firebase key file not found at {firebase_path}")
                self.firebase_service_account_json = "{}"

settings = Settings()
