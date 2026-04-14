from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gestor-identidades-python"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str
    auth_issuer: str
    auth_audience: str
    auth_jwks_url: str
    expiration_job_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
