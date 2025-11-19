from dotenv import load_dotenv

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding = "utf-8",
    )

    redis_host: str
    redis_port: int
    redis_db: int
    test_redis_db: int
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


settings = Settings()


if __name__ == "__main__":
    print("📦 Loaded settings:")
    for key, value in settings.model_dump().items():
        masked = "***" if "secret" in key or "password" in key else value
        print(f"  {key}: {masked}")

