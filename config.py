from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "MobilePay"
    environment: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "mobilepay"
    secret_key: str = "CHANGE_ME_BEFORE_DEPLOYING"
    admin_api_key: str = "CHANGE_ME_ADMIN_KEY"
    cors_origins: str = "http://localhost:8000"
    otp_provider: str = "demo"
    enable_demo_otp: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_verify_service_sid: str = ""
    made_by: str = "Mohammad Hakeeb"
    instagram_url: str = "https://instagram.com/"
    apk_download_url: str = ""
    promo_user_text: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
