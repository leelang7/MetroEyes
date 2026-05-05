# MetroEyes lite_server — torch 없이 즉시 작동하는 backend
# Build:  docker build -t metroeyes:latest .
# Run:    docker run -p 8765:8765 -e SEOUL_OPENDATA_API_KEY=xxx metroeyes:latest --demo
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 — 최소 (websockets만)
RUN pip install --no-cache-dir websockets

# 소스 복사
COPY src/cv/lite_server.py /app/src/cv/lite_server.py
COPY src/cv/__init__.py /app/src/cv/__init__.py

# 환경 변수 (기본 .env 가 있으면 로드)
ENV PYTHONUNBUFFERED=1

# 8765 포트 노출
EXPOSE 8765

# Health check — /health endpoint 30초 간격
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://localhost:8765/health', timeout=2); sys.exit(0)" || exit 1

# 기본 실행 — --demo 모드로 시작 (CV 없이 BEV 5Hz + warm seed + 5분 자동 incident)
CMD ["python", "-m", "src.cv.lite_server", "--port", "8765", "--host", "0.0.0.0", "--demo"]
