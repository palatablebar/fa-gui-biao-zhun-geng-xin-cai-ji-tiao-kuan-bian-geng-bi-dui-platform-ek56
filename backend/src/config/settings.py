"""集中配置：全部来自环境变量，默认值与 .env.example 保持一致。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # 品牌与业务
    brand: str = "lawdelta"
    org_name: str = "安衡合规咨询 · 法规监测组"

    # 数据库
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "lawdelta"
    db_user: str = "lawdelta"
    db_password: str = "lawdelta_pw_2026"
    db_schema: str = "lawdelta"

    # 安全
    jwt_secret: str = "lawdelta-jwt-secret-change-me-2026"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 120
    refresh_token_days: int = 7

    # 运行时
    redis_url: str = "redis://localhost:6379/0"
    seed_demo: bool = True
    rate_limit_diff_per_minute: int = 12
    rate_limit_crawl_per_minute: int = 8
    rate_limit_default_per_minute: int = 240

    # 算法阈值（可与 fixtures 一起复现；前端只展示后端回传值）
    align_match_threshold: float = 0.55
    align_change_threshold: float = 0.86

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
