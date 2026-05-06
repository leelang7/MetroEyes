# MetroEyes

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-7dd3d3.svg)](LICENSE)
[![ROI](https://img.shields.io/badge/ROI%20v3-347x-10b981.svg)](frontend/pitch.html)
[![Social Value](https://img.shields.io/badge/Social_Value-%E2%82%A9139.3B%2Fyr-7dd3d3.svg)](frontend/pitch.html)
[![EDA](https://img.shields.io/badge/EDA%20v3%20R²-0.931-f59e0b.svg)](scripts/eda_carload_v3_real.py)
[![Cycles](https://img.shields.io/badge/Auto_Cycles-290-a78bfa.svg)](CHANGELOG.md)
[![Lang](https://img.shields.io/badge/lang-ko%20·%20en%20·%20zh%20·%20ja-ef4444.svg)](frontend/passenger_app/index.html)

> *"As Tesla sees the road as BEV, MetroEyes sees the entire urban transit network."*

🇰🇷 [한국어 README](README.md)

**Live demo**: https://leelang7.github.io/MetroEyes/

**Headline KPIs (Policy ROI v3, 30% response rate)**:
- Net social value **₩139.3B/yr** · ROI **347x** · Infra ₩400M (134 priority stations)
- Saved time 473.4M min/yr · Cap flattening −0.66%p · Line 2 alone 157M min
- **Tiered incentive 4 levels** (₩100/₩200/₩300/₩400) — backend auto-bonus, EDA-mapped

**3 EDA real-data validations**:
- **Dispersion**: σ −9.0% / peak avg −13.5% / off-peak +5.6% / ratio 1.78→1.46
- **OD asymmetry**: Samsung(Trade Center) OFF/ON 12.4x (morning arrival) / City Hall ON/OFF 4.9x (evening departure)
- **Transfer asymmetry**: Chungmuro Line 4 +0.56 vs Line 3 −1.00 (diff +1.56) / Yeonsinnae +1.44

**Entry**: [`frontend/index.html`](frontend/index.html) — 8-card hub (📊 Policy Report / 🎬 Integrated Demo / 🚇 Operator / 📱 Citizen / 🛠 Debug)

---

## What is MetroEyes?

**3-axis integrated system**: Subway/Bus BEV CV + Real-time city data + Citizen redistribution incentives.

A single citizen action (₩200 reward) → backend krw accumulation → operator console live ROI x →
backend incident broadcast → citizen route avoidance notice. **5-stage two-sided closed loop**.

## 263 Auto Cycles Accumulated (D-7, 2026-05-13 deadline)

- ✅ **Two-sided value chain 8 stages** (CV → city → decision → OD match → transfer match → citizen tiered → backend auto-bonus → ROI live)
- ✅ **Demo fail-safe 8 layers**: `--demo` + 30s injector + 5min sticky bar + backend join summary + admin click + warm seed + Docker compose + GitHub Actions CI
- ✅ **4 languages** (ko/en/zh/ja) **11-page parity** + Web Speech + ARIA + **5-page foreigner welcome toast**
- ✅ **Mobile responsive** (4 operator + ads + citizen PWA) + safe-area-inset
- ✅ **3 EDA real-data validations**: GBR R²=0.931 / Dispersion (σ −9% / peak −13.5%) / OD asymmetry (Samsung 12x) / Transfer (Chungmuro +1.56)
- ✅ **11 pages integrated** + ROI interactive slider + **±15% sensitivity CI band**
- ✅ **PDF print-friendly** pitch.html + FAQ 6 + Global comparison + dispersion 4-KPI cards
- ✅ **Tiered incentive policy** — ₩100 / ₩200 / ₩300 (OD priority) / ₩400 (transfer station) **with backend auto-bonus**
- ✅ **A* + K-means(K=4) + Hungarian** emergency evacuation — single-exit baseline cost reduction quantified
- ✅ **9 REST endpoints** (health/roi_curve/impact/incidents/dispersion/od/transfer/policy_summary/openapi) + **OpenAPI 3.0 spec**
- ✅ **A* + K-means(K=4) + Hungarian 1:1 exit matching** for emergency evacuation (cost reduction vs single-exit baseline quantified)
- ✅ **OpenAPI 3.0 spec** (`/api/openapi.yaml`) — Swagger/Redoc/Postman auto-import

**5-min presentation video capture guide**: [`docs/RECORDING_GUIDE.md`](docs/RECORDING_GUIDE.md) — 10-stage sequence + OBS settings + Korean narration.

**Presentation materials (6 docs)**:
- [`docs/SLIDES.html`](docs/SLIDES.html) — Hancom 16:9 slides (PDF exportable)
- [`docs/SLIDES_DECK.md`](docs/SLIDES_DECK.md) — slide texts (Hancom copy-paste)
- [`docs/PROPOSAL.md`](docs/PROPOSAL.md) — primary proposal body
- [`docs/INNOVATION_TRIZ.md`](docs/INNOVATION_TRIZ.md) — TRIZ 6 contradictions analysis
- [`docs/ARCHITECTURE_VIEW.html`](docs/ARCHITECTURE_VIEW.html) — 4-layer system diagram
- [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md) — primary submission checklist

## Quickstart (Demo without CV model)

```bash
python -m src.cv.lite_server --port 8765 --demo
```

→ Fake BEV tracks broadcast at 5Hz + automatic impact seed (warm 12 + 5-min auto incidents).
All 10 pages immediately go live (KPI / sparkline / time-of-day distribution / incident timeline).

**One-line Docker (backend + frontend)**:
```bash
docker compose up -d
```
→ backend `:8765` + frontend `:5173` instantly. `.env` auto-loaded. Identical verification in any environment.

## Full Real-Data Pipeline

1. Backend (CV): `python -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280`
2. Video feeder: `python scripts/feed_video.py`
3. (Optional) ngrok: `ngrok http 8765`
4. All pages share live signal from same backend.

## Data Sources — 9 public APIs

**Seoul Open Data Plaza (7)**:
- `citydata` — integrated city data (110 POIs, minute-level)
- `citydata_ppltn` — population/congestion (e.g. Seongsu surge detection)
- `SPOP_DAILYSUM_JACHI` — district daily population
- `CardSubwayStatsNew` — hourly board/alight (monthly)
- `realtimeStationArrival` — TOPIS real-time arrivals
- `ListPublicReservationCulture` — cultural events
- `bikeList` / `tbCycleStationInfo` — Seoul Bike

**Public Data Portal / External (2)**:
- Bus arrival BIS (separate key)
- Naver Search + Anthropic Claude — auto context on population surge

**In-house CV backend**:
- YOLO11n + BoT-SORT + homography BEV → ws broadcast
- `--demo` mode — fake BEV tracks 5Hz (no CV model needed)
- Live external API routing + auto LLM context on surge detection

## Differentiators vs Global Policies

| City | Policy | Incentive | Granularity | Limitation |
|---|---|---|---|---|
| 🇬🇧 London | Off-Peak (~30% discount) | Fixed | Station-level RFID | No car-level distribution |
| 🇯🇵 Tokyo | Off-Peak Suica pass | Monthly flat | Commute-segment stats | No real-time guidance |
| 🇸🇬 Singapore | GP-S pilot (2018) — 25¢ | One-time | EZ-Link card | No real-time car data, ~5% response |
| 🇰🇷 **MetroEyes** | Distribution-rate tiered (5%p +₩100, 30%p +₩200) | **Real-time car-level** | In-house CV BEV (30%~150% capacity) | **ROI 347x at 30% response** |

**Differentiator**: London/Tokyo/Singapore all use **station-level** statistics. MetroEyes is the first
**car-level BEV CV** + **distribution-rate tiered reward** + **backend cumulative live ROI** —
3-axis integrated system where one citizen action = one operator KPI metric.

## Open REST API v1 + OpenAPI 3.0

backend `lite_server.py` exposes 7 endpoints — all CORS-enabled:

| Endpoint | Response | Use |
|---|---|---|
| `GET /health` | system status (api/cv/incidents/msg) | health check |
| `GET /api/v1/roi_curve` | 81 samples 0~80% ROI | external policy sim |
| `GET /api/v1/impact` | cumulative redistribution impact | live KPI |
| `GET /api/v1/incidents` | 4 incident counts + 30 events | live monitoring |
| `GET /api/v1/dispersion` | static σ/peak/offpeak validation + live response-rate estimate | dispersion visualization |
| `GET /api/v1/od_asymmetry` | current-hour AM/PM auto-match + top 5 priority stations | operator policy priority |
| `GET /api/v1/transfer_priority` | transfer-station inter-line asymmetry diff top 5 (current AM/PM) | transfer-flow policy |
| `GET /api/openapi.yaml` | OpenAPI 3.0 spec | Swagger/Redoc/Postman auto-import |

```bash
# Example: ROI curve fetch
curl http://localhost:8765/api/v1/roi_curve | jq '.curve | map(select(.rate == 0.30))'

# Example: Dispersion effect (static + live)
curl -s http://localhost:8765/api/v1/dispersion | jq '{static: .static, live: .live}'

# Example: Current-hour OD priority (AM 7~11 → arrival / PM 17~21 → departure)
curl -s http://localhost:8765/api/v1/od_asymmetry | jq '{type: .priority_type, stations: .priority_stations | map(.station)}'

# Example: Download OpenAPI 3.0 spec
curl -o openapi.yaml http://localhost:8765/api/openapi.yaml
```

## Run Policy ROI v3

```bash
python scripts/policy_roi_v3.py
```

Outputs:
- `outputs/policy_roi_v3_report.json` — 5 scenarios + line-by-line saved-minutes matrix
- `outputs/policy_roi_v3_matrix.png` — 9 lines × 24 hours heatmap

**Improvements over v2**: Line cap-saturation (Line 1 0.55 vs 9 1.10) + commute response asymmetry
(7-9 AM 0.7 vs 5-7 PM 1.0) + cap flattening effect. At 30% response, v2 ₩28.3B → **v3 ₩139.3B/yr (5x precision)**.

Detailed analysis: [`frontend/pitch.html`](frontend/pitch.html) (single-page quantitative report)

## License

Apache 2.0 (see [LICENSE](LICENSE))

Includes:
- YOLO11n + BoT-SORT (Ultralytics, AGPL-3.0)
- websockets (Python, BSD)
- Three.js (MIT)
- Anthropic Claude API (commercial)
- Naver Search API (commercial)
- Seoul OpenAPI (CC-BY)

## Contact

- Lee Sang-cheol · leescvsir@gmail.com
- 2026 Seoul Big Data Competition (Startup Track) submission · Deadline 2026-05-13
