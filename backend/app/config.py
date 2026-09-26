from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Database
    database_url: str = "sqlite:///./eduplat.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Storage
    storage_type: str = "local"
    storage_path: str = "./storage"
    s3_bucket: str | None = None
    s3_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    
    # API Keys
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    
    # JWT
    secret_key: str = "change-this-to-a-random-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Application
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    # Supported languages
    supported_languages: List[str] = [
        "en",  # English
        "hi",  # Hindi
        "ta",  # Tamil
        "te",  # Telugu
        "kn",  # Kannada
        "bn",  # Bengali
    ]
    
    language_names: dict = {
        "en": "English",
        "hi": "हिन्दी",
        "ta": "தமிழ்",
        "te": "తెలుగు",
        "kn": "ಕನ್ನಡ",
        "bn": "বাংলা",
    }


settings = Settings()
