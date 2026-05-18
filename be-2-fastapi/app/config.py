from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fastapi_port: int = 8002
    fastapi_cors_origins: str = "http://localhost:5172"

    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    # Optional: separate API app registration audience (defaults to client id).
    azure_ad_api_audience: str = ""

    postgres_host: str = ""
    postgres_port: int = 5432
    postgres_user: str = "sso"
    postgres_password: str = ""
    postgres_db: str = "sso_learning"

    @property
    def azure_auth_enabled(self) -> bool:
        return bool(self.azure_ad_tenant_id.strip() and self.azure_ad_client_id.strip())

    @property
    def azure_issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_ad_tenant_id}/v2.0"

    @property
    def azure_jwks_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_ad_tenant_id}/discovery/v2.0/keys"

    @property
    def azure_audience(self) -> str:
        return (self.azure_ad_api_audience or self.azure_ad_client_id).strip()

    @property
    def database_url(self) -> str | None:
        if not self.postgres_host.strip():
            return None
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
