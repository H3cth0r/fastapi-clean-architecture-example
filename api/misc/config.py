from enum import Enum

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class EnvName(str, Enum):
    production = "production"
    staging = "staging"
    development = "development"
    testing = "testing"


class Config(BaseSettings):
    ENVIRONMENT: EnvName
    POSTGRES_URL: PostgresDsn
    TEST_POSTGRES_BASE_URL: PostgresDsn | None = None
    PORT: int = 8000
    DEFAULT_API_KEY: str = "dev-test-api-key-12345"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def is_production(self) -> bool:
        return self.ENVIRONMENT == EnvName.production


config = Config()

TORTOISE_ORM = {
    "connections": {"default": str(config.POSTGRES_URL)},
    "apps": {
        "models": {
            "models": ["api.data.postgres_models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
