from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = True

    class Config:
        env_file = "..\local.env"
        env_file_encoding = "utf-8"

settings = Settings()