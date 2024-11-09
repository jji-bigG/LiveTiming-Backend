from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "LiveTiming Backend"
    DEBUG: bool = True
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = 0
    
    # RabbitMQ settings
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "livetiming")
    RABBITMQ_PASS: str = os.getenv("RABBITMQ_PASS", "livetiming123")
    
    # Queue settings
    TIMING_QUEUE: str = "timing_data"
    SENSOR_QUEUE: str = "sensor_data"
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()