# MetroEyes

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-7dd3d3.svg)](LICENSE)
[![ROI](https://img.shields.io/badge/ROI%20v3-347x-10b981.svg)](frontend/pitch.html)
[![Social Value](https://img.shields.io/badge/Social_Value-%E2%82%A9139.3B%2Fyr-7dd3d3.svg)](frontend/pitch.html)
[![EDA](https://img.shields.io/badge/EDA%20v3%20R²-0.931-f59e0b.svg)](scripts/eda_carload_v3_real.py)
[![Cycles](https://img.shields.io/badge/Auto_Cycles-450-a78bfa.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/regression_tests-316_guards-10b981.svg)](tests/)
[![Lang](https://img.shields.io/badge/lang-ko%20·%20en%20·%20zh%20·%20ja-ef4444.svg)](frontend/passenger_app/index.html)

> *"As Tesla sees the road as BEV, MetroEyes sees the entire urban transit network."*

🇰🇷 [한국어 README](README.md)

**Live demo**: https://leelang7.github.io/MetroEyes/

**Run locally** (clone → demo in 30 seconds):
```bash
git clone https://github.com/leelang7/MetroEyes.git && cd MetroEyes
make install      # pip install -r requirements.txt (cycle 421)
make verify       # ship-gate 10/10 + pytest 273 guards (10s)
make demo         # backend lite-server :8765 --demo (no CV model)
```
Windows PowerShell: `./scripts/dday.ps1 -Quick` · Mac/Linux bash: `./scripts/dday.sh --quick`

---

## 💡 For Reviewers — Core in 5 minutes

> First-time viewers: start with these 5 artifacts — all 1:1 mapped to 1st/2nd round scoring weights.

| Priority | Asset | One-line | Time |
|---:|---|---|---:|
| **1** | [📊 frontend/onepager.html](frontend/onepager.html) | A4 1-Pager — headline KPIs / 6 differentiators / 4-city comparison / BM **(4 languages)** | 1 min |
| **2** | [🎬 frontend/demo.html](frontend/demo.html) | 5-min integrated auto-demo — 4 panels + 14-stage SCRIPT | 5 min |
| **3** | [📈 frontend/pitch.html](frontend/pitch.html) | Quantitative report — Monte Carlo CI + per-line ROI + line×hour matrix | 5 min |
| **4** | [🎯 docs/SUBMISSION_INDEX.md](docs/SUBMISSION_INDEX.md) | Eval criteria ↔ artifact ↔ CI guard self-score (1st 105 + 2nd 100) | 3 min |
| **5** | [💬 docs/QA_PREPARATION.md](docs/QA_PREPARATION.md) | 18 anticipated Q&A + 30-sec self-pitch (5 categories) | 5 min |

**TL;DR**: In-house CV BEV + 9 public APIs + citizen redistribution incentives — 3-axis integrated system.
Policy ROI v3 + Monte Carlo 1,000 simulations → social value **₩139.3B/yr [CI ₩106B~₩181B]**.
Line 2 ROI 708x — instant policy answer. 8-layer fail-safe + 316 regression guards + 10 public APIs + 4-language i18n production-grade.

**Additional docs (ops/incident)**: [📕 docs/RUNBOOK.md](docs/RUNBOOK.md) — 9 scenarios 1-line recovery · [📖 docs/PROPOSAL.md](docs/PROPOSAL.md) — detailed proposal v3 · [📋 docs/FORM_DATA.md](docs/FORM_DATA.md) — pre-filled myBox submission form data

---

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

## 428 Auto Cycles Accumulated (D-4, 2026-05-13 deadline)

- ✅ **Two-sided value chain 8 stages** (CV → city → decision → OD match → transfer match → citizen tiered → backend auto-bonus → ROI live)
- ✅ **Demo fail-safe 8 layers**: `--demo` + 30s injector + 5min sticky bar + backend join summary + admin click + warm seed + Docker compose + GitHub Actions CI
- ✅ **4 languages** (ko/en/zh/ja) **11-page parity** + Web Speech + ARIA + **5-page foreigner welcome toast**
- ✅ **Mobile responsive** (4 operator + ads + citizen PWA) + safe-area-inset
- ✅ **3 EDA real-data validations**: GBR R²=0.931 / Dispersion (σ −9% / peak −13.5%) / OD asymmetry (Samsung 12x) / Transfer (Chungmuro +1.56)
- ✅ **11 pages integrated** + ROI interactive slider + **±15% sensitivity CI band**
- ✅ **PDF print-friendly** pitch.html + FAQ 6 + Global comparison + dispersion 4-KPI cards
- ✅ **Tiered incentive policy** — ₩100 / ₩200 / ₩300 (OD priority) / ₩400 (transfer station) **with backend auto-bonus**
- ✅ **A* + K-means(K=4) + Hungarian** emergency evacuation — single-exit baseline cost reduction quantified
- ✅ **10 REST endpoints** (health/roi_curve/impact/incidents/dispersion/od/transfer/policy_summary/openapi/docs) + **OpenAPI 3.0 spec**
- ✅ **CI 15 jobs + 316 pytest regression guards** (cycle 318-450): OpenAPI(4) + ROI v3(5) + dispersion(6) + OD/transfer(6) + bonus(6) + figs(3) + pitch(6) + impact(5) + cycle 356-427 new 165 (LLM/env/A*/PWA/demo/i18n/ROI panel/heatmap/narration/onepager/proposal v3/SLIDES v3/Monte Carlo CI/RUNBOOK/QA/SUBMISSION_INDEX/reviewer guide/changelog/ship-gate/dday.ps1·sh/Makefile/3D OpenFreeMap/citydata real fetch) — advertised KPIs ↔ code ↔ figs ↔ deck ↔ canonical JSON all auto-synced
- ✅ **Canonical KPI drift auto-blocked** (cycle 375): ad 1,393억 / 347x / Line 2 157M / CI [1,064~1,808] all artifacts simultaneously consistent — D-day issue like cycle 374 auto-detected
- ✅ **Submission ship-gate** (cycle 380): `python scripts/submission_check.py --ci` 1-sec 12 items PASS/WARN/FAIL — every push auto-verifies submission-ready
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

backend `lite_server.py` exposes 10 endpoints (REST API v1 9 + auto docs UI 1) — all CORS-enabled:

| Endpoint | Response | Use |
|---|---|---|
| `GET /health` | system status (api/cv/incidents/msg) | health check |
| `GET /api/v1/roi_curve` | 81 samples 0~80% ROI | external policy sim |
| `GET /api/v1/impact` | cumulative redistribution impact + tier_counts | live KPI |
| `GET /api/v1/incidents` | 6 incident counts (incl. IDEA-7/8 priority_seat/bottleneck) + 30 events | live monitoring |
| `GET /api/v1/dispersion` | static σ/peak/offpeak validation + live response-rate estimate | dispersion visualization |
| `GET /api/v1/od_asymmetry` | current-hour AM/PM auto-match + top 5 priority stations | operator policy priority |
| `GET /api/v1/transfer_priority` | transfer-station inter-line asymmetry diff top 5 (current AM/PM) | transfer-flow policy |
| `GET /api/v1/policy_summary` | tier definition + live impact + dispersion + **incident_breakdown 6 type** + EDA | Excel/Power BI single poll |
| `GET /api/openapi.yaml` | OpenAPI 3.0 spec | Swagger/Redoc/Postman auto-import |
| `GET /api/docs` | auto HTML spec page | curl/Postman alternative |

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

- Lee Seok-chang
- 2026 Seoul Big Data Competition (Startup Track) submission · Deadline 2026-05-13
