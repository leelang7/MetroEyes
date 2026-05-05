# MetroEyes Mobile App (Flutter)

> 시민 PWA의 네이티브 폰 앱 버전. backend `lite_server` (port 8765) 와 wss/ws WebSocket 연결.

## 기능

- 가까운 역 GPS 자동 매칭 (12개 핫스팟 · `_stations` 리스트)
- BEV 트랙 라이브 수신 (`bev_socket.dart` WebSocket 클라이언트)
- 시민 PWA 와 동일 backend `impact_log` / `arrival_query` / `population_query` 송수신
- backend `--demo` 모드와 즉시 호환 (warm seed + 5분 자동 incident)

## 빠른 시작

```bash
flutter pub get
flutter run -d chrome   # 웹 (Chrome)
flutter run -d windows  # Windows desktop
flutter build apk       # Android APK (외부 폰 시연)
```

## 백엔드 URL

- 로컬: `ws://localhost:8765`
- 원격 (ngrok): `wss://app.allthatai.kr` (또는 본인 도메인)
- 159 사이클 누적 backend 와 호환 (8 REST endpoint):
  - `/health` 시스템 상태 (api/cv/incidents/msg/tier_counts)
  - `/api/v1/impact` 누적 분산 임팩트 + tier_counts
  - `/api/v1/incidents` 사고 timeline
  - `/api/v1/roi_curve` ROI 81 샘플
  - `/api/v1/dispersion` σ/peak/offpeak 정적 + 라이브 추정
  - `/api/v1/od_asymmetry` 현 시각 OD 우선 TOP 5
  - `/api/v1/transfer_priority` 환승역 비대칭 TOP 5
  - `/api/openapi.yaml` OpenAPI 3.0 spec
  - `/api/docs` 자동 HTML 명세

## 공유 백엔드와 호환

웹 (`frontend/passenger_app`) + 폰 (`mobile_app`) 모두 동일 ws 메시지 사용:
- `population_query` `{poi}` → `{type:'population', congest_lvl, ppltn_min/max}`
- `arrival_query` `{stationName, line}` → `{type:'arrival', items}`
- `impact_log` `{station, car, saved_pct, krw}` → backend가 자동 차등 보상 가산 (OD +₩100 / 환승 +₩200) → broadcast `impact_summary` (tier_counts 포함)
- `incident_log` `{ev_type, severity, msg, source}` → broadcast `incident_summary`

자세한 명세: `http://localhost:8765/api/docs` 또는 OpenAPI 3.0 임포트 (`/api/openapi.yaml`).

## 차등 보상 정책

폰 앱에서 station 이름이 backend의 OD/환승 우선순위 명단에 있으면 자동으로 보상 가산:
- 일반 분산: ₩200
- OD 우선순위 역 (현 시각 AM 7~11 / PM 17~21): ₩200 + ₩100 = **₩300**
- 환승역 (충무로/연신내/동대문 등 37곳): ₩200 + ₩200 = **₩400**

UI에서 chip 으로 표시하거나 backend `impact_summary.tier_counts` 분포 polling 으로 참조 가능.

## 라이센스

Apache 2.0 — 상위 [LICENSE](../LICENSE) 참조.
