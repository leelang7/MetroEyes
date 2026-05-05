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
- 100 사이클 누적 backend 와 호환:
  - `/health` 시스템 상태
  - `/api/v1/impact` 누적 분산 임팩트
  - `/api/v1/incidents` 사고 timeline
  - `/api/v1/roi_curve` ROI 81 샘플
  - `/api/docs` 자동 HTML 명세

## 공유 백엔드와 호환

웹 (`frontend/passenger_app`) + 폰 (`mobile_app`) 모두 동일 ws 메시지 사용:
- `population_query` `{poi}` → `{type:'population', congest_lvl, ppltn_min/max}`
- `arrival_query` `{stationName, line}` → `{type:'arrival', items}`
- `impact_log` `{station, car, saved_pct, krw}` → broadcast `impact_summary`
- `incident_log` `{ev_type, severity, msg, source}` → broadcast `incident_summary`

자세한 명세: `http://localhost:8765/api/docs`

## 라이센스

Apache 2.0 — 상위 [LICENSE](../LICENSE) 참조.
