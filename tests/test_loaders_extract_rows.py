"""src/data_pipeline/loaders.py — extract_rows 단위 테스트 (cycle 506).

네트워크 불필요: extract_rows 는 순수 dict 파싱 함수.
서울 OpenAPI 응답 구조 { "<ServiceName>": { "row": [...] } } 파싱 정확성 검증.
"""
from __future__ import annotations

import pytest


def test_extract_rows_typical_response() -> None:
    """일반적인 서울 OpenAPI 응답에서 row 추출."""
    from src.data_pipeline.loaders import extract_rows
    payload = {"CardSubwayTime": {"list_total_count": 2, "row": [{"A": 1}, {"A": 2}]}}
    rows = extract_rows(payload)
    assert rows == [{"A": 1}, {"A": 2}]


def test_extract_rows_empty_row() -> None:
    """row 가 빈 리스트 → 빈 리스트 반환."""
    from src.data_pipeline.loaders import extract_rows
    payload = {"SomeService": {"row": []}}
    rows = extract_rows(payload)
    assert rows == []


def test_extract_rows_raises_on_missing_row() -> None:
    """row 키 없는 응답 → KeyError."""
    from src.data_pipeline.loaders import extract_rows
    payload = {"SomeService": {"RESULT": {"CODE": "INFO-000"}}}
    with pytest.raises(KeyError):
        extract_rows(payload)


def test_extract_rows_raises_on_empty_dict() -> None:
    """빈 dict → KeyError."""
    from src.data_pipeline.loaders import extract_rows
    with pytest.raises(KeyError):
        extract_rows({})


def test_extract_rows_none_row_returns_empty() -> None:
    """row 가 None → 빈 리스트."""
    from src.data_pipeline.loaders import extract_rows
    payload = {"Svc": {"row": None}}
    # None 이면 or [] 로 빈 리스트 반환
    rows = extract_rows(payload)
    assert rows == []


def test_extract_rows_multiple_services_picks_first() -> None:
    """여러 서비스 키가 있어도 row 가 있는 첫 번째 반환."""
    from src.data_pipeline.loaders import extract_rows
    payload = {
        "Meta": {"RESULT": {"CODE": "INFO-000"}},
        "Data": {"row": [{"val": 42}]},
    }
    rows = extract_rows(payload)
    assert rows == [{"val": 42}]


def test_extract_rows_row_with_many_items() -> None:
    """100개 항목 row → 정확히 100개 반환."""
    from src.data_pipeline.loaders import extract_rows
    data = [{"i": i} for i in range(100)]
    payload = {"LargeService": {"row": data}}
    rows = extract_rows(payload)
    assert len(rows) == 100
    assert rows[0]["i"] == 0
    assert rows[-1]["i"] == 99
