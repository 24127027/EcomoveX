from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DEST_DB_NAME: str = "ecomovex_destinations"
    USER_DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: str = "142857"
    
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000," 

    HUGGINGFACE_API_KEY: str = ""

    CLIMATIQ_API_KEY: str = ""

settings = Settings()