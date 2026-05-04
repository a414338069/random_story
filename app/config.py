from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DATABASE_PATH: str = "app/data/rebirth.db"
    CORS_ORIGINS: str = "*"
    MAX_EVENTS_PER_GAME: int = 60
    CACHE_TTL: int = 1800
