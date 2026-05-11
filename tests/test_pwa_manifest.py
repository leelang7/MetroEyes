"""frontend/passenger_app/manifest.webmanifest PWA 설치 회귀 가드 (cycle 529).

MetroEyes 시민 앱 PWA 설치 필수 조건:
- name / short_name / description
- start_url / scope / display=standalone
- theme_color #7dd3d3 (브랜드 teal)
- background_color #04060a (앱 배경)
- icons 2종 (192x192 / 512x512)
- orientation=portrait / lang=ko
"""
from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "frontend/passenger_app/manifest.webmanifest"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_exists() -> None:
    """manifest.webmanifest 파일 존재."""
    assert MANIFEST.exists(), "passenger_app/manifest.webmanifest 없음"


def test_manifest_name() -> None:
    """name 필드 — MetroEyes 포함."""
    assert "MetroEyes" in _manifest()["name"]


def test_manifest_short_name() -> None:
    """short_name = 'MetroEyes'."""
    assert _manifest()["short_name"] == "MetroEyes"


def test_manifest_display_standalone() -> None:
    """display = 'standalone' (PWA 설치 필수)."""
    assert _manifest()["display"] == "standalone"


def test_manifest_theme_color() -> None:
    """theme_color = #7dd3d3 (MetroEyes 브랜드 teal)."""
    assert _manifest()["theme_color"].lower() == "#7dd3d3"


def test_manifest_background_color() -> None:
    """background_color = #04060a (앱 배경)."""
    assert _manifest()["background_color"].lower() == "#04060a"


def test_manifest_start_url() -> None:
    """start_url 정의 — PWA 시작점."""
    assert "start_url" in _manifest()
    assert _manifest()["start_url"] != ""


def test_manifest_icons_2() -> None:
    """아이콘 2종 이상 (192x192 / 512x512)."""
    icons = _manifest()["icons"]
    assert len(icons) >= 2, f"아이콘 {len(icons)}개 < 2"


def test_manifest_icon_sizes() -> None:
    """아이콘 192x192 / 512x512 사이즈 존재."""
    sizes = {i["sizes"] for i in _manifest()["icons"]}
    assert "192x192" in sizes, "192x192 아이콘 없음"
    assert "512x512" in sizes, "512x512 아이콘 없음"


def test_manifest_orientation_portrait() -> None:
    """orientation = 'portrait' (세로 모드)."""
    assert _manifest().get("orientation") == "portrait"
