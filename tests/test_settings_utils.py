"""src/utils/settings.py 유틸리티 단위 테스트 (cycle 509).

- PROJECT_ROOT: 프로젝트 루트 경로 유효성
- load_env: Env 인스턴스 반환 + 기본값 검증
- load_config: 존재하지 않는 config → FileNotFoundError
- load_config("default"): DictConfig 반환 (seoul_opendata 섹션 포함)
"""
from __future__ import annotations

from pathlib import Path


def test_project_root_exists() -> None:
    """PROJECT_ROOT 디렉토리 실제 존재."""
    from src.utils.settings import PROJECT_ROOT
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.is_dir(), f"PROJECT_ROOT 존재하지 않음: {PROJECT_ROOT}"


def test_project_root_has_src() -> None:
    """PROJECT_ROOT/src 존재 — 프로젝트 루트 정확히 가리킴."""
    from src.utils.settings import PROJECT_ROOT
    assert (PROJECT_ROOT / "src").is_dir(), "PROJECT_ROOT/src 없음 — 잘못된 경로"


def test_load_env_returns_env_instance() -> None:
    """load_env() → Env 인스턴스."""
    from src.utils.settings import load_env, Env
    env = load_env()
    assert isinstance(env, Env)


def test_load_env_default_api_port() -> None:
    """기본 api_port=8000."""
    from src.utils.settings import load_env
    env = load_env()
    assert env.api_port == 8000


def test_load_env_default_log_level() -> None:
    """기본 log_level='INFO'."""
    from src.utils.settings import load_env
    env = load_env()
    assert env.log_level == "INFO"


def test_load_env_keys_are_strings() -> None:
    """API 키 필드는 항상 str (None 아님)."""
    from src.utils.settings import load_env
    env = load_env()
    assert isinstance(env.seoul_opendata_api_key, str)
    assert isinstance(env.anthropic_api_key, str)


def test_load_config_missing_raises() -> None:
    """없는 config name → FileNotFoundError."""
    from src.utils.settings import load_config
    import pytest
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config_12345")


def test_load_config_default_returns_dictconfig() -> None:
    """load_config('default') → OmegaConf DictConfig."""
    from src.utils.settings import load_config
    from omegaconf import DictConfig
    cfg = load_config("default")
    assert isinstance(cfg, DictConfig)


def test_load_config_default_has_seoul_opendata() -> None:
    """default.yaml에 seoul_opendata 섹션 존재."""
    from src.utils.settings import load_config
    cfg = load_config("default")
    assert hasattr(cfg, "seoul_opendata"), "default.yaml seoul_opendata 섹션 누락"
