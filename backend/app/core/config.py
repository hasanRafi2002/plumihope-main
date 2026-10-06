from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    jwt_secret: str
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 30

    s3_endpoint: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str

    payment_provider: str = "sandbox"
    payment_api_key: str = ""
    payment_webhook_secret: str = ""
    # DEV ONLY: accept unsigned webhooks for provider "sandbox". Ignored when app_env == "production".
    payment_webhook_allow_unsigned_sandbox: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
