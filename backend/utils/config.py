from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    #Database connection settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ecomovex_db"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"

    # --- Security/Authentication Settings ---
    # The key used to sign JWTs (Keep this secret and robust)
    SECRET_KEY: str = "super_secret_key"
    # The hashing algorithm used for JWTs
    ALGORITHM: str = "HS256"

    # List of front-end origins allowed to access the API
    # Default value as a fallback if the enviroment variable isn't set
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000," 

    # --- External API Keys ---
    # Google Maps Platform API key for Places, Geocoding, Directions
    GOOGLE_MAPS_API_KEY: str = ""
    
    # OpenAI API key for GPT models (chatbot)
    OPENAI_API_KEY: str = ""
    
    # Google Gemini API key (alternative to OpenAI)
    GEMINI_API_KEY: str = ""
    
    # Carbon Interface API key for emissions calculations
    CARBON_INTERFACE_API_KEY: str = ""
    
    # AI Provider selection (openai or gemini)
    AI_PROVIDER: str = "openai"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.local",
        env_file_encoding="utf-8",
    )

settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
