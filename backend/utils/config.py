from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ecomoveX"
    DB_USER: str = "postgres"
    DB_PASS: str = ""

    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: str = "http://localhost:3000,https://ecomovex.onrender.com,"
    
    GOOGLE_API_KEY: str = ""
    CLIMATIQ_API_KEY: str = ""

    SUSTAINABILITY_DATA_API_CLIENT_ID: str = ""
    SUSTAINABILITY_DATA_API_CLIENT_SECRET: str = ""

    GCS_BUCKET_NAME: str = "ecomovex"
    GOOGLE_APPLICATION_CREDENTIALS: Path = Path("etc/secrets/service-account.json")

    OPEN_ROUTER_API_KEY: str = "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"
    
    FIRST_ADMIN_EMAIL: str = ""
    OPEN_ROUTER_MODEL_NAME: str = "meta-llama/llama-3.3-70b-instruct"

    BREEAM_USERNAME: str = ""
    BREEAM_PASSWORD: str = ""
    
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_STARTTLS: bool = True
    SMTP_TIMEOUT: int = 30

settings = Settings()