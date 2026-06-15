from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class AppConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 7678
    debug: bool = False
    title: str = "P Tools API"
    version: str = "0.1.0"
    secret_key: str = "change-me-to-a-random-string"


class DatabaseConfig(BaseSettings):
    host: str = "10.126.126.4"
    port: int = 3306
    user: str = "root"
    password: str = "123456"
    name: str = "p_tools"

    @property
    def url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}?charset=utf8mb4"
        )


class GuangyaConfig(BaseSettings):
    access_token: str | None = None
    refresh_token: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    guangya: GuangyaConfig = Field(default_factory=GuangyaConfig)


def load_yaml_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml_config(data: dict) -> None:
    existing = load_yaml_config()
    existing.update(data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, allow_unicode=True, default_flow_style=False)


@lru_cache
def get_settings() -> Settings:
    config_data = load_yaml_config()
    # YAML 可能把纯数字值解析为 int，转成 str 兼容
    if "app" in config_data and isinstance(config_data["app"], dict):
        for k, v in config_data["app"].items():
            if isinstance(v, int):
                config_data["app"][k] = str(v)
    return Settings(**config_data)


settings = get_settings()
