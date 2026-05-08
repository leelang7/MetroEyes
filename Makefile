# MetroEyes Makefile (cycle 419, install added cycle 421) — third-platform parity for dday.ps1 / dday.sh
# Usage: make <target>
#
# Common targets:
#   make          → quick verify (alias for `make verify`)
#   make install  → 첫 셋업 (pip install -r requirements.txt)
#   make verify   → submission_check --ci + pytest (10초 미만)
#   make full     → EDA 재생성 + 풀 ship-gate (~3분, D-1 권장)
#   make regen    → EDA 4종 재생성만 (canonical KPI drift 발생 시)
#   make test     → pytest 회귀 가드만 (245+ tests)
#   make demo     → backend lite-server --demo 시작 (CV 모델 없이)
#   make clean    → outputs/ 캐시 정리

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.DEFAULT_GOAL := verify
.PHONY: install verify full regen test demo clean help

install:
	@echo "=== MetroEyes 첫 셋업 (cycle 421) ==="
	@echo "Python: $(shell $(PYTHON) --version 2>&1)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo ""
	@echo "✅ 의존성 설치 완료 — 다음:  make verify"

verify:
	@echo "=== submission_check --ci (1초 < 10 항목) ==="
	@$(PYTHON) scripts/submission_check.py --ci
	@echo ""
	@echo "=== pytest 회귀 가드 (244+ tests) ==="
	@$(PYTHON) -m pytest tests/ --ignore=tests/test_smoke.py -q

full:
	@echo "=== EDA 재생성 (4 scripts) + 풀 ship-gate ==="
	@$(PYTHON) scripts/policy_roi_v3.py
	@$(PYTHON) scripts/eda_line_priority_roi.py
	@$(PYTHON) scripts/eda_line_hour_priority.py
	@$(PYTHON) scripts/eda_co2_savings.py
	@$(PYTHON) -m pytest tests/ --ignore=tests/test_smoke.py -q
	@$(PYTHON) scripts/submission_check.py

regen:
	@echo "=== EDA 4종 재생성 (canonical KPI drift fix) ==="
	@$(PYTHON) scripts/policy_roi_v3.py
	@$(PYTHON) scripts/eda_line_priority_roi.py
	@$(PYTHON) scripts/eda_line_hour_priority.py
	@$(PYTHON) scripts/eda_co2_savings.py
	@echo "✅ frontend/figs/*.json 갱신 완료 — 광고 자료 동기화 확인 권장"

test:
	@$(PYTHON) -m pytest tests/ --ignore=tests/test_smoke.py -v

demo:
	@echo "=== backend lite-server demo mode (no CV model) ==="
	@$(PYTHON) -m src.cv.lite_server --port 8765 --demo

clean:
	@echo "=== outputs/ 캐시 정리 (figs/ 는 보존) ==="
	@rm -rf outputs/__pycache__ outputs/*.tmp 2>/dev/null || true
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Python cache + outputs tmp 정리 완료"

help:
	@echo "MetroEyes Makefile (cycle 419, install cycle 421)"
	@echo ""
	@echo "Targets:"
	@echo "  make install        first-time setup (pip install)"
	@echo "  make / make verify  Quick D-day check (10s)"
	@echo "  make full           EDA regen + full ship-gate (~3min)"
	@echo "  make regen          EDA 4 scripts only"
	@echo "  make test           pytest 245+ guards"
	@echo "  make demo           start backend lite-server --demo"
	@echo "  make clean          remove __pycache__ + tmp"
	@echo ""
	@echo "Cross-platform alternatives:"
	@echo "  Windows PowerShell  ./scripts/dday.ps1 -Quick"
	@echo "  Mac/Linux bash      ./scripts/dday.sh --quick"
	@echo ""
	@echo "Docs: docs/RUNBOOK.md (장애 9 시나리오) · docs/SUBMISSION_GUIDE.md (D-day)"
