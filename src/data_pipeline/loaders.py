"""서울 OpenAPI → DataFrame + parquet 캐시 얇은 헬퍼.

서울 OpenAPI 응답 구조:
    { "<ServiceName>": { "list_total_count": N, "RESULT": {...}, "row": [ {...}, ... ] } }

페이지네이션 한도: 한 번에 1~1000 행. 큰 일자/긴 기간은 page 단위로 누적.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.data_pipeline.seoul_opendata import SeoulOpenDataClient
from src.utils.settings import PROJECT_ROOT

CACHE_DIR = PROJECT_ROOT / "data" / "processed"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def extract_rows(payload: dict[str, Any]) -> list[dict]:
    """응답 dict의 첫 번째 'row' 컨테이너를 반환."""
    for v in payload.values():
        if isinstance(v, dict) and "row" in v:
            return v["row"] or []
    raise KeyError(f"row 없음: keys={list(payload.keys())}")


def paged_fetch(
    service: str,
    *extra: str,
    page: int = 1000,
    max_rows: int = 50_000,
) -> list[dict]:
    rows: list[dict] = []
    with SeoulOpenDataClient() as c:
        start = 1
        while start <= max_rows:
            end = min(start + page - 1, max_rows)
            payload = c.fetch(service, start, end, *extra)
            chunk = extract_rows(payload)
            rows.extend(chunk)
            if len(chunk) < page:
                break
            start += page
    return rows


def fetch_to_parquet(
    service: str,
    *extra: str,
    cache_name: str,
    force: bool = False,
    page: int = 1000,
    max_rows: int = 50_000,
) -> pd.DataFrame:
    """서비스 호출 → 전체 페이지 누적 → parquet 캐시. 두 번째부턴 캐시 히트."""
    cache = CACHE_DIR / f"{cache_name}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)
    rows = paged_fetch(service, *extra, page=page, max_rows=max_rows)
    df = pd.DataFrame(rows)
    df.to_parquet(cache, index=False)
    return df
