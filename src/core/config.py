from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvEnum(StrEnum):
    development = "development"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )

    environment: EnvEnum = EnvEnum.development

    echo_sql: bool = False
    secret_key: str = "local"
    cookie_expire_minutes: int = 60 * 24 * 365
    frontend_url: str = "http://localhost:5173"
    frontend_oauth_error_url: str = "http://localhost:5173/oauth-error"

    google_client_id: str = "test-client-id"
    google_client_secret: str = "test-client-secret"
    google_redirect_uri: str = "http://localhost:5173/api/v1/auth/google/callback"

    postgres_user: str = "local"
    postgres_password: str = "local"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "local"

    @property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}"
            f":{self.postgres_password}"
            f"@{self.postgres_host}"
            f":{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @property
    def test_database_url(self) -> str:
        return f"{self.database_url}_test"

    @property
    def migration_database_url(self) -> str:
        return (
            self.database_url
            if self.environment == EnvEnum.production
            else f"{self.database_url}_migration"
        )

    @property
    def reset_db_on_startup(self) -> bool:
        return self.environment == EnvEnum.development and self.postgres_host == "db"

    @property
    def is_production(self) -> bool:
        return self.environment == EnvEnum.production

    @property
    def is_development(self) -> bool:
        return self.environment == EnvEnum.development


settings = Settings()
