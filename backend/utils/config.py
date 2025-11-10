from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DEST_DB_NAME: str = "ecomovex_destinations"
    USER_DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: str = "142857"
    
    # JWT settings
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    # CORS settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000," 

    #For Huggingface API (text generation)
    HUGGINGFACE_API_KEY: str = ""

    #For Climatiq API (carbon emissions)
    CLIMATIQ_API_KEY: str = ""

    #For Google Cloud Storage
    GCS_BUCKET_NAME: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: Path = Path("service-account.json")

settings = Settings()