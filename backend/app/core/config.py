from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    GEMINI_API_KEY: str
    GEMINI_RPD_LIMIT: int = 450
    UPLOAD_DIR: str
    COOKIE_SECURE: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:5173"


settings = Settings()
