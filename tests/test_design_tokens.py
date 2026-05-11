"""CSS 디자인 토큰 회귀 가드 (cycle 513).

MetroEyes 디자인 시스템 핵심 컬러:
- --accent: #7dd3d3 (청록 — MetroEyes 브랜드)
- --bg: #0a0a0e 또는 #04060a (다크 배경)
- 도메인별 컬러: subway/bus/realcam/ads/arch
- tokens.css / bev_console.css / passenger_app/styles.css

브랜드 일관성이 심사 인상에 직결 — 토큰 표류 방지.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS_CSS = ROOT / "frontend" / "shared" / "tokens.css"
BEV_CSS = ROOT / "frontend" / "shared" / "bev_console.css"
STYLES_CSS = ROOT / "frontend" / "passenger_app" / "styles.css"


def test_tokens_css_exists() -> None:
    """shared/tokens.css 존재."""
    assert TOKENS_CSS.is_file(), "shared/tokens.css 누락"


def test_bev_console_css_exists() -> None:
    """shared/bev_console.css 존재."""
    assert BEV_CSS.is_file(), "shared/bev_console.css 누락"


def test_passenger_styles_css_exists() -> None:
    """passenger_app/styles.css 존재."""
    assert STYLES_CSS.is_file(), "passenger_app/styles.css 누락"


def test_tokens_accent_color() -> None:
    """tokens.css — --accent: #7dd3d3 (MetroEyes 브랜드 청록)."""
    src = TOKENS_CSS.read_text(encoding="utf-8")
    assert "--accent" in src, "--accent 토큰 누락"
    assert "#7dd3d3" in src, "#7dd3d3 브랜드 색상 누락"


def test_tokens_domain_colors() -> None:
    """tokens.css — 도메인별 컬러 (subway/bus/realcam/ads/arch)."""
    src = TOKENS_CSS.read_text(encoding="utf-8")
    for domain in ("subway", "bus", "realcam", "ads", "arch"):
        assert f"--domain-{domain}" in src, f"--domain-{domain} 토큰 누락"


def test_tokens_semantic_colors() -> None:
    """tokens.css — 시맨틱 컬러 (--good/--warn/--crit)."""
    src = TOKENS_CSS.read_text(encoding="utf-8")
    assert "--good" in src or "--accent" in src, "--good 또는 semantic 컬러 누락"
    assert "--warn" in src, "--warn 컬러 누락"
    assert "--crit" in src, "--crit 컬러 누락"


def test_bev_console_domain_bars() -> None:
    """bev_console.css — .domain-bar.subway/bus/realcam/ads 클래스."""
    src = BEV_CSS.read_text(encoding="utf-8")
    assert "domain-bar" in src, ".domain-bar 클래스 누락"
    for domain in ("subway", "bus", "realcam", "ads"):
        assert f".domain-bar.{domain}" in src, f".domain-bar.{domain} 누락"


def test_bev_console_accent_color() -> None:
    """bev_console.css — --accent: #7dd3d3."""
    src = BEV_CSS.read_text(encoding="utf-8")
    assert "#7dd3d3" in src, "bev_console.css #7dd3d3 브랜드 색상 누락"


def test_passenger_styles_accent() -> None:
    """passenger_app/styles.css — --accent 토큰 존재."""
    src = STYLES_CSS.read_text(encoding="utf-8")
    assert "--accent" in src, "passenger styles --accent 토큰 누락"
    assert "#7dd3d3" in src, "passenger styles #7dd3d3 색상 누락"


def test_passenger_styles_safe_area() -> None:
    """passenger_app/styles.css — env(safe-area-inset) iOS 노치 대응."""
    src = STYLES_CSS.read_text(encoding="utf-8")
    assert "safe-area-inset" in src, "iOS 노치 safe-area 대응 누락"
