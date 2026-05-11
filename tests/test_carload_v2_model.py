"""scripts/eda_carload_v2.py 호선 점유 모델 v2 단위 테스트 (cycle 521).

순수 numpy — 네트워크/데이터 불필요:
- LINE_META: 9호선 메타데이터 dict
- TYPES: 호선 유형 4종 리스트
- synth_target(line, h): v1 재현 점유율 추정
- build_dataset(): 1080 샘플 (9×24×5 노이즈)

심사 기준 '공공데이터 활용·실현가능성': 호선 분류 모델 신뢰성.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_line_meta_9_lines() -> None:
    """LINE_META — 1~9호선 모두 정의."""
    from eda_carload_v2 import LINE_META
    for i in range(1, 10):
        assert f"{i}호선" in LINE_META, f"{i}호선 누락"


def test_line_meta_fields() -> None:
    """LINE_META 각 항목 — 필수 필드 존재."""
    from eda_carload_v2 import LINE_META
    for line, m in LINE_META.items():
        for field in ("cars", "cap", "headway", "cap_ratio", "hub", "type"):
            assert field in m, f"{line} 필드 {field} 누락"


def test_types_four_categories() -> None:
    """TYPES — 4가지 유형 포함."""
    from eda_carload_v2 import TYPES
    assert len(TYPES) == 4, f"TYPES 길이 {len(TYPES)} ≠ 4"
    for t in ("office", "residen", "hub", "leisure"):
        assert t in TYPES, f"유형 {t} 누락"


def test_synth_target_positive() -> None:
    """synth_target("2호선", 8) > 0 (AM 피크)."""
    from eda_carload_v2 import synth_target
    v = synth_target("2호선", 8)
    assert v > 0, "2호선 8시 점유율 = 0"


def test_synth_target_am_peak_gt_night() -> None:
    """synth_target AM 피크 (8시) > 심야 (3시)."""
    from eda_carload_v2 import synth_target
    am = synth_target("2호선", 8)
    night = synth_target("2호선", 3)
    assert am > night, f"AM {am:.3f} ≤ 야간 {night:.3f}"


def test_synth_target_pm_peak_gt_night() -> None:
    """synth_target PM 피크 (18시) > 심야 (3시)."""
    from eda_carload_v2 import synth_target
    pm = synth_target("2호선", 18)
    night = synth_target("2호선", 3)
    assert pm > night, f"PM {pm:.3f} ≤ 야간 {night:.3f}"


def test_synth_target_bounded() -> None:
    """synth_target → [0.05, 1.5] 범위."""
    from eda_carload_v2 import synth_target, LINE_META
    for line in LINE_META:
        for h in range(24):
            v = synth_target(line, h)
            assert 0.05 <= v <= 1.5, f"{line} {h}시 점유율 {v:.3f} 범위 초과"


def test_build_dataset_length() -> None:
    """build_dataset() 길이 = 9 × 24 × 5 = 1080."""
    from eda_carload_v2 import build_dataset
    rows = build_dataset()
    assert len(rows) == 1080, f"샘플 수 {len(rows)} ≠ 1080"


def test_build_dataset_fields() -> None:
    """build_dataset() 각 행 — 필수 필드."""
    from eda_carload_v2 import build_dataset
    rows = build_dataset()
    for field in ("line", "hour", "occ_pct", "cap_ratio", "is_peak_am"):
        assert field in rows[0], f"필드 {field} 누락"
