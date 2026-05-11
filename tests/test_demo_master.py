"""frontend/demo.html 통합 시연 마스터 페이지 회귀 가드 (cycle 505).

5분 자동 재생 4-패널 시연:
- 운영자 콘솔(지하철) + 시민 PWA + 버스 운영자 + 광고 단가 + 실카메라 + 정책 ROI
- 시연 시작 버튼 + 타이머 + 진행 바
- 4언어 토글 (I18N_DEMO) + 첫 방문 환영 toast
- 사회적 가치 라이브 카운터 (demo-impact)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "frontend" / "demo.html"


def _html() -> str:
    return DEMO.read_text(encoding="utf-8")


def test_demo_html_exists() -> None:
    """frontend/demo.html 존재."""
    assert DEMO.is_file(), "frontend/demo.html 누락"


def test_demo_brand_metroeyes() -> None:
    """MetroEyes 통합 시연 브랜드."""
    html = _html()
    assert "MetroEyes" in html, "MetroEyes 브랜드 누락"
    assert "통합 시연" in html or "Integrated Demo" in html, "통합 시연 제목 누락"


def test_demo_start_button() -> None:
    """시연 시작 버튼 + id=start."""
    html = _html()
    assert 'id="start"' in html, "start 버튼 element 누락"
    assert "시연 시작" in html, "시연 시작 텍스트 누락"


def test_demo_timer_element() -> None:
    """타이머 element id=timer."""
    html = _html()
    assert 'id="timer"' in html, "timer element 누락"


def test_demo_progress_bar() -> None:
    """진행 바 (demo-bar) 존재."""
    html = _html()
    assert "demo-bar" in html, "demo-bar 진행 바 누락"


def test_demo_4panel_iframes() -> None:
    """4-패널 iframe — 운영자/시민/버스/카메라."""
    html = _html()
    for panel_id in ("if-op", "if-pwa", "if-bus", "if-cam"):
        assert panel_id in html, f"패널 iframe {panel_id} 누락"
    # 실제 src 경로
    for src in ("operator_web/index.html", "passenger_app/index.html",
                "operator_web/bus.html", "operator_web/realbev.html"):
        assert src in html, f"iframe src {src} 누락"


def test_demo_pitch_panel() -> None:
    """정책 ROI 패널 (if-pitch → pitch.html)."""
    html = _html()
    assert "if-pitch" in html, "if-pitch 패널 누락"
    assert "pitch.html" in html, "pitch.html 참조 누락"


def test_demo_stage_banner() -> None:
    """시나리오 단계 배너 id=stage."""
    html = _html()
    assert 'id="stage"' in html, "stage-banner element 누락"
    assert "stage-banner" in html, "stage-banner 클래스 누락"


def test_demo_welcome_toast_4lang() -> None:
    """첫 방문 환영 toast — 4언어 메시지 (ko/en/zh/ja)."""
    html = _html()
    assert "demo-welcome" in html, "demo-welcome toast element 누락"
    # 4언어 환영 메시지
    assert "5분" in html or "5-min" in html, "5분 자동재생 안내 누락"
    for lang_key in ("ko", "en", "zh", "ja"):
        assert f"'{lang_key}'" in html or f'"{lang_key}"' in html, \
            f"{lang_key} 언어 toast 누락"


def test_demo_i18n_dict_4lang() -> None:
    """I18N_DEMO 딕셔너리 — 4언어 브랜드/버튼 문자열."""
    html = _html()
    assert "I18N_DEMO" in html, "I18N_DEMO 딕셔너리 누락"
    # 브랜드 문자열 (각 언어)
    assert "Integrated Demo" in html, "en 브랜드 누락"
    assert "综合演示" in html or "統合デモ" in html, "zh/ja 브랜드 누락"


def test_demo_live_impact_counter() -> None:
    """라이브 사회적 가치 카운터 — demo-impact / dh-cnt / dh-val."""
    html = _html()
    assert "demo-impact" in html, "demo-impact 카운터 누락"
    assert "dh-cnt" in html, "dh-cnt (분산 인원) 누락"
    assert "dh-val" in html, "dh-val (절감 가치) 누락"


def test_demo_lang_toggle_button() -> None:
    """언어 토글 버튼 id=lang-toggle."""
    html = _html()
    assert "lang-toggle" in html, "lang-toggle 버튼 누락"
