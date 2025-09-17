from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "HTX Image Pipeline"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite:///./data.db"
    CAPTION_MODEL: str = "disabled"  # e.g., 'nlpconnect/vit-gpt2-image-captioning'

    class Config:
        env_file = ".env"


settings = Settings()
