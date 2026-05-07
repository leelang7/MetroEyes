"""제출 직전 한 번에 — KPI / figs / 회귀 가드 / 다국어 / API 정합성 자동 검증 (cycle 367).

사용:
    python scripts/submission_check.py

D-5 마감 직전 발생할 수 있는 실수 유형 자동 차단:
    1. README/pitch 광고 KPI 와 실제 JSON 리포트 수치 불일치
    2. pitch.html 가 참조하는 figs/* 누락 / 0-byte
    3. 회귀 테스트 fail (빠진 가드 항목 노출 위험)
    4. 4언어 (ko/en/zh/ja) 키 누락
    5. 핵심 산출물 (CHANGELOG, LICENSE, PROPOSAL) 부재

Exit code:
    0 = PASS · 1 = WARN (주의) · 2 = FAIL (제출 차단)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent

# Windows cp949 콘솔 한글 정상 출력
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass


@dataclass
class CheckResult:
    name: str
    severity: str   # 'PASS' / 'WARN' / 'FAIL'
    detail: str = ""


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    def ok(self, name: str, detail: str = "") -> None:
        self.results.append(CheckResult(name, "PASS", detail))

    def warn(self, name: str, detail: str) -> None:
        self.results.append(CheckResult(name, "WARN", detail))

    def fail(self, name: str, detail: str) -> None:
        self.results.append(CheckResult(name, "FAIL", detail))

    @property
    def n_pass(self) -> int: return sum(1 for r in self.results if r.severity == "PASS")
    @property
    def n_warn(self) -> int: return sum(1 for r in self.results if r.severity == "WARN")
    @property
    def n_fail(self) -> int: return sum(1 for r in self.results if r.severity == "FAIL")


# ============== 검사 항목 ==============

def check_required_files(rep: Report) -> None:
    """1. 필수 산출물 존재 + 비어있지 않음."""
    required = [
        "README.md", "README.en.md", "LICENSE", "CHANGELOG.md",
        "docs/PROPOSAL.md", "docs/SLIDES.html", "docs/SLIDES_DECK.md",
        "frontend/pitch.html", "frontend/index.html",
        "frontend/passenger_app/index.html", "frontend/admin.html",
        "frontend/operator_web/realbev.html", "frontend/operator_web/ad_pricing.html",
        "frontend/demo.html",
        "scripts/policy_roi_v3.py", "scripts/eda_line_priority_roi.py",
        "src/cv/lite_server.py", "src/cv/tesla_bev.py",
        ".github/workflows/ci.yml",
    ]
    for f in required:
        p = ROOT / f
        if not p.exists():
            rep.fail("required_files", f"missing: {f}")
        elif p.stat().st_size < 100:
            rep.warn("required_files", f"suspiciously small ({p.stat().st_size}B): {f}")
        else:
            pass
    if rep.n_fail == 0 and rep.n_warn == 0:
        rep.ok("required_files", f"{len(required)} 파일 모두 존재")


def check_kpi_consistency(rep: Report) -> None:
    """2. README/pitch 광고 KPI ↔ 실제 JSON 리포트 일치."""
    # 정책 v3 — 1,393억 / 347x / 473.4M분
    roi_path = ROOT / "outputs" / "policy_roi_v3_report.json"
    if not roi_path.exists():
        rep.warn("kpi_v3_report", f"missing {roi_path} — run scripts/policy_roi_v3.py")
        return
    try:
        d = json.loads(roi_path.read_text(encoding="utf-8"))
    except Exception as e:
        rep.fail("kpi_v3_report", f"unreadable: {e}")
        return
    net = d.get("net_value_b", 0)
    roi = d.get("roi_x", 0)
    minutes_m = d.get("minutes_saved_yr", 0) / 1_000_000
    # 광고 1,393억 ±1%
    if abs(net - 1393) / 1393 > 0.01:
        rep.fail("kpi_net_value", f"광고 1,393억 vs 실측 {net:.0f}억")
    else:
        rep.ok("kpi_net_value", f"1,393억 일치 (실측 {net:.0f}억)")
    # ROI 347x ±2%
    if abs(roi - 347) / 347 > 0.02:
        rep.fail("kpi_roi", f"광고 347x vs 실측 {roi:.0f}x")
    else:
        rep.ok("kpi_roi", f"347x 일치 (실측 {roi:.0f}x)")
    # 절감 분 473.4M ±1%
    if abs(minutes_m - 473.4) / 473.4 > 0.01:
        rep.fail("kpi_saved_min", f"광고 473.4M분 vs 실측 {minutes_m:.1f}M분")
    else:
        rep.ok("kpi_saved_min", f"473.4M분 일치 (실측 {minutes_m:.1f}M분)")
    # CI band — 30% 광고 1,393억이 95% CI 안에
    ci_path = ROOT / "frontend" / "figs" / "policy_roi_v3_ci_band.json"
    if ci_path.exists():
        cd = json.loads(ci_path.read_text(encoding="utf-8"))
        ci30 = cd["scenarios"].get("0.30")
        if ci30 and ci30["net_b_p5"] <= 1393 <= ci30["net_b_p95"]:
            rep.ok("kpi_ci_band", f"30% CI [{ci30['net_b_p5']:.0f}~{ci30['net_b_p95']:.0f}] 1,393억 포함")
        else:
            rep.fail("kpi_ci_band", f"30% CI {ci30} 광고 1,393억 안 포함")


def check_dispersion_kpi(rep: Report) -> None:
    """3. 분산 EDA — σ −9% / 피크 −13.5%."""
    p = ROOT / "frontend" / "figs" / "dispersion_sim_report.json"
    if not p.exists():
        rep.warn("kpi_dispersion", f"missing {p}")
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    s = d.get("sigma_reduction_pct", 0)
    if -9.5 <= s <= -8.5:
        rep.ok("kpi_dispersion_sigma", f"σ −9% 일치 (실측 {s:.1f}%)")
    else:
        rep.fail("kpi_dispersion_sigma", f"σ 광고 −9% vs 실측 {s:.1f}%")


def check_pitch_figs_present(rep: Report) -> None:
    """4. pitch.html 의 모든 <img src='figs/*'> 가 실재."""
    pitch = ROOT / "frontend" / "pitch.html"
    if not pitch.exists():
        rep.fail("pitch_figs", "pitch.html 부재")
        return
    html = pitch.read_text(encoding="utf-8")
    figs = re.findall(r"<img\s+src=[\"']figs/([^\"']+)[\"']", html)
    figs = list(set(figs))
    missing = []
    empty = []
    for f in figs:
        p = ROOT / "frontend" / "figs" / f
        if not p.exists():
            missing.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)
    if missing:
        rep.fail("pitch_figs", f"missing figs: {missing}")
    elif empty:
        rep.fail("pitch_figs", f"empty figs (0 bytes): {empty}")
    else:
        rep.ok("pitch_figs", f"{len(figs)} figs 모두 존재 + non-empty")


def check_pytest_pass(rep: Report) -> None:
    """5. 회귀 테스트 통과 (smoke 제외 — torch 의존성)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--ignore=tests/test_smoke.py", "-q", "--tb=no"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        rep.fail("pytest_pass", "pytest 60초 timeout")
        return
    out = result.stdout + result.stderr
    if result.returncode != 0:
        rep.fail("pytest_pass", f"exit {result.returncode}\n  {out[-400:]}")
        return
    m = re.search(r"(\d+) passed", out)
    n = int(m.group(1)) if m else 0
    if n < 50:
        rep.warn("pytest_pass", f"only {n} tests passed — expected ≥50")
    else:
        rep.ok("pytest_pass", f"{n} tests passed")


def check_4lang_parity(rep: Report) -> None:
    """6. PWA i18n 4언어 (ko/en/zh/ja) 모두 핵심 키 보유 + tab_subway 등."""
    pwa = ROOT / "frontend" / "passenger_app" / "index.html"
    if not pwa.exists():
        rep.fail("i18n_4lang", "PWA missing")
        return
    html = pwa.read_text(encoding="utf-8")
    # 4 언어 마커 — tab_subway 키가 4 lang 블록에 모두 등장 (multiline dotall)
    for lang, flag in [("ko", "🇰🇷"), ("en", "🇺🇸"), ("zh", "🇨🇳"), ("ja", "🇯🇵")]:
        # lang: { ... tab_subway: '...' ... } — non-greedy 까지 nest 무시
        m = re.search(rf"\b{lang}:\s*\{{[\s\S]*?tab_subway:", html)
        if not m:
            rep.fail("i18n_4lang", f"PWA 언어 {lang} ({flag}) tab_subway 키 누락")
            return
    rep.ok("i18n_4lang", "PWA 4언어 (ko/en/zh/ja) 정상")


def check_ci_jobs_present(rep: Report) -> None:
    """7. CI workflow 가 cycle 356-366 모든 회귀 가드 실행."""
    ci_yml = ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_yml.exists():
        rep.fail("ci_workflow", "ci.yml 부재")
        return
    yml = ci_yml.read_text(encoding="utf-8")
    required_tests = [
        "test_ad_llm_context", "test_env_live_panel", "test_evac_strengthen",
        "test_pwa_picker", "test_demo_orchestration", "test_i18n_admin_ad",
        "test_admin_line_roi_panel", "test_line_priority_roi", "test_roi_ci_band",
        "test_eda_dispersion", "test_eda_od_transfer", "test_bonus_krw",
        "test_pitch_structure", "test_impact_summary", "test_openapi_spec",
        "test_policy_roi_v3", "test_figures_present",
    ]
    missing = [t for t in required_tests if t not in yml]
    if missing:
        rep.fail("ci_workflow", f"CI 누락 테스트: {missing}")
    else:
        rep.ok("ci_workflow", f"{len(required_tests)} 회귀 가드 CI 자동 실행")


def check_changelog_recent(rep: Report) -> None:
    """8. CHANGELOG 가 최근 cycle 까지 업데이트되었는지 (cycle 360+ 라벨)."""
    cl = ROOT / "CHANGELOG.md"
    if not cl.exists():
        rep.warn("changelog", "CHANGELOG.md 부재")
        return
    txt = cl.read_text(encoding="utf-8")
    # cycle 350 이상 등장하는지 (현재 366)
    nums = [int(m) for m in re.findall(r"cycle\s+(\d{3,4})", txt, re.IGNORECASE)]
    if not nums:
        rep.warn("changelog", "cycle 번호 없음 — CHANGELOG 업데이트 권장")
    elif max(nums) < 350:
        rep.warn("changelog", f"최근 cycle {max(nums)} — 366+ 까지 추가 권장")
    else:
        rep.ok("changelog", f"최근 cycle {max(nums)}")


def check_python_imports(rep: Report) -> None:
    """9. 핵심 backend 모듈 import 가능 (구문 오류 즉시 차단)."""
    modules = ["src.cv.lite_server", "src.cv.tesla_bev"]
    for m in modules:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {m}"],
                cwd=ROOT, capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                err = result.stderr.strip().split("\n")[-1]
                rep.fail("python_imports", f"{m} 구문/의존성 오류: {err}")
                return
        except Exception as e:
            rep.fail("python_imports", f"{m}: {e}")
            return
    rep.ok("python_imports", f"{len(modules)} 백엔드 모듈 import OK")


# ============== runner ==============

CHECKS: list[Callable[[Report], None]] = [
    check_required_files,
    check_kpi_consistency,
    check_dispersion_kpi,
    check_pitch_figs_present,
    check_4lang_parity,
    check_ci_jobs_present,
    check_changelog_recent,
    check_python_imports,
    check_pytest_pass,   # 가장 무거우므로 마지막
]


def main() -> int:
    print("=" * 72)
    print(" MetroEyes 제출 직전 자동 검증 — D-5 (2026-05-13 마감)")
    print("=" * 72)
    rep = Report()
    for fn in CHECKS:
        try:
            fn(rep)
        except Exception as e:
            rep.fail(fn.__name__, f"검사 자체 예외: {type(e).__name__}: {e}")
    # 출력
    print()
    for r in rep.results:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[r.severity]
        print(f"  {icon} [{r.severity}] {r.name}")
        if r.detail and r.severity != "PASS":
            for line in r.detail.split("\n"):
                print(f"          {line}")
    print()
    print(f"  요약: {rep.n_pass} PASS · {rep.n_warn} WARN · {rep.n_fail} FAIL")
    print()
    if rep.n_fail > 0:
        print("  ❌ FAIL — 제출 전 위 항목 수정 필수")
        return 2
    if rep.n_warn > 0:
        print("  ⚠️  WARN — 제출 가능하나 위 항목 점검 권장")
        return 1
    print("  ✅ PASS — 제출 준비 완료 🎉")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
