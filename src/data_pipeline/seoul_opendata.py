"""서울 열린데이터광장 클라이언트 (스켈레톤).

엔드포인트 명세:
    http://openapi.seoul.go.kr:8088/{KEY}/{TYPE}/{SERVICE}/{START}/{END}/...

대회 필수 활용 데이터셋:
    - 지하철 혼잡도 (편성 단위) → 우리는 칸 단위로 세분화
    - 실시간 열차 위치
    - 지하역사 실내 공기질 (CO₂) → BEV 약지도 신호
    - 호선/역/시간대별 승하차
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.settings import load_config, load_env


class SeoulOpenDataClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        env = load_env()
        cfg = load_config("default").seoul_opendata
        self.api_key = api_key or env.seoul_opendata_api_key
        if not self.api_key:
            raise ValueError("SEOUL_OPENDATA_API_KEY 미설정")
        self.base_url = base_url or cfg.base_url
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self) -> "SeoulOpenDataClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def fetch(
        self,
        service: str,
        start: int = 1,
        end: int = 100,
        *extra: str,
        fmt: str = "json",
    ) -> dict[str, Any]:
        parts = [self.api_key, fmt, service, str(start), str(end), *extra]
        url = f"{self.base_url}/" + "/".join(quote(p, safe="") for p in parts)
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # smoke test: python -m src.data_pipeline.seoul_opendata
    with SeoulOpenDataClient() as c:
        data = c.fetch("CardSubwayStatsNew", 1, 5, "20260101")
        print(list(data.keys()))
