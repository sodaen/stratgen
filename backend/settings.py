from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_HOST: str = Field("127.0.0.1", env="HOST")
    APP_PORT: int = Field(8000, env="PORT")

    API_KEY: str = Field("", env="STRATGEN_API_KEY")

    QDRANT_URL: str = Field("http://127.0.0.1:6333", env="QDRANT_URL")
    QDRANT_API_KEY: str = Field("", env="QDRANT_API_KEY")
    CHECK_QDRANT_COMPAT: bool = Field(True, env="CHECK_QDRANT_COMPAT")

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
