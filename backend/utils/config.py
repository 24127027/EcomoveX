from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "your_database"
    DB_USER: str = "your_username"
    DB_PASS: str = "your_password"
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / "local.env",
        env_file_encoding="utf-8",
    )

settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
