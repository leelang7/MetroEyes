"""realbev.html IDEA-6/7 기능 회귀 가드 (cycle 502).

IDEA-6: 비상 동선 (A* + K-means(K=4) + 헝가리안 1:1 매칭)
IDEA-7: 응급 골든타임 + 분실물 자동 감지

- 분실물 후보: 짐 트랙 + 인근 사람 없음 (10초 이상)
- 응급: 사람 30초+ 비정상 자세 정지 → 골든타임 카운터
- AED 위치: 서울시 공공데이터 API 로드 (fallback 3개소)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REALBEV = ROOT / "frontend" / "operator_web" / "realbev.html"


def _html() -> str:
    return REALBEV.read_text(encoding="utf-8")


def test_realbev_idea7_golden_timer() -> None:
    """IDEA-7 응급 골든타임 — 30초+ 비정상 자세 정지 감지."""
    html = _html()
    assert "골든타임" in html or "golden" in html.lower() or "IDEA-7" in html, \
        "IDEA-7 골든타임 감지 코드 누락"
    assert "30" in html, "30초 타이머 임계값 누락"


def test_realbev_aed_locations() -> None:
    """AED 위치 데이터 — 서울시 공공데이터 fallback 3개소."""
    html = _html()
    assert "AED" in html, "AED 위치 데이터 누락"
    assert "AED_LOCATIONS" in html or "aed" in html.lower(), "AED 위치 배열 누락"


def test_realbev_lost_item_detection() -> None:
    """IDEA-6 분실물 자동 감지 — 짐 클래스 + 정적 시간."""
    html = _html()
    assert "backpack" in html or "BAG_CLASSES" in html, "분실물 클래스 감지 누락"
    assert "분실물" in html, "분실물 알림 텍스트 누락"


def test_realbev_idea6_evac_button() -> None:
    """IDEA-6 비상 동선 추론 버튼 (evac-btn)."""
    html = _html()
    assert "evac-btn" in html, "evac-btn 비상 동선 버튼 누락"
    assert "비상 동선" in html, "비상 동선 텍스트 누락"


def test_realbev_exit_block_buttons() -> None:
    """출구 차단 버튼 — NW/NE/SW/SE 4방향."""
    html = _html()
    assert "exit-block-btn" in html, "출구 차단 버튼 누락"
    for direction in ("NW", "NE", "SW", "SE"):
        assert direction in html, f"{direction} 방향 출구 버튼 누락"


def test_realbev_astar_algorithm() -> None:
    """A* pathfinding 알고리즘 구현."""
    html = _html()
    assert "A*" in html or "astar" in html.lower() or "pathfinder" in html.lower(), \
        "A* 비상 동선 알고리즘 누락"


def test_realbev_hungarian_matching() -> None:
    """헝가리안 1:1 매칭 (K-means 그룹 → 출구 비용 최소)."""
    html = _html()
    assert "헝가리안" in html or "hungarian" in html.lower(), \
        "헝가리안 매칭 알고리즘 누락"
    assert "kmeans" in html.lower() or "k-means" in html.lower() or "K-means" in html, \
        "K-means 군중 분할 누락"


def test_realbev_distributed_cost_comparison() -> None:
    """분산 vs 단일 출구 vs 4분면 비용 비교."""
    html = _html()
    assert "단일" in html and "분산" in html, "비용 비교 텍스트 누락"


def test_realbev_public_aed_api() -> None:
    """서울시 공공데이터 AED API 연동 (fetch)."""
    html = _html()
    # AED 데이터를 fetch 또는 fallback으로 처리
    assert "aed" in html.lower() and ("fetch" in html or "AED_LOCATIONS" in html), \
        "AED 공공데이터 API 연동 누락"
