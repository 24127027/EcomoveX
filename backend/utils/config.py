from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"

    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000," 

    GOOGLE_MAPS_API_KEY: str = "AIzaSyDaOulQACiJzBfqumbsqg_-vKha8fCnL-s"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    CARBON_INTERFACE_API_KEY: str = ""
    AI_PROVIDER: str = "openai"
    HUGGINGFACE_API_KEY: str = ""

settings = Settings()