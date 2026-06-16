from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = "development"
    APP_URL: str = "http://localhost:8000"
    WEB_URL: str = "https://www.webcolegios.com/clararincon/"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
