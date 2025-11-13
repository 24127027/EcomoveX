from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DEST_DB_NAME: str = "ecomovex_destinations"
    USER_DB_NAME: str = "ecomovex_user"
    DB_USER: str = "postgres"
    DB_PASS: str = ""
    
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000," 

    HUGGINGFACE_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    CLIMATIQ_API_KEY: str = ""
    
    SUSTAINABILITY_DATA_API_CLIENT_ID: str = ""
    SUSTAINABILITY_DATA_API_CLIENT_SECRET: str = ""
    

    #For Google Cloud Storage
    GCS_BUCKET_NAME: str = "ecomovex"
    GOOGLE_APPLICATION_CREDENTIALS: str = "utils/service-account.json"

settings = Settings()