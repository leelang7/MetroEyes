"""환경변수 + YAML 설정 로더."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from omegaconf import DictConfig, OmegaConf
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


class Env(BaseSettings):
    """`.env` 로딩. 시크릿/환경별 값만 여기에."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    seoul_opendata_api_key: str = ""
    anthropic_api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    device: str = "cuda"


@lru_cache
def load_env() -> Env:
    return Env()


@lru_cache
def load_config(name: str = "default") -> DictConfig:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    return OmegaConf.load(path)
