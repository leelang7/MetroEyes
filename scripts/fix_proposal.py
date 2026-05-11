"""상세기획서 HTML 구조 정렬 + 폰트 + 스테일 수정."""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT / "docs" / "proposal_deck.html"

content = SRC.read_text(encoding="utf-8")

# ── 1. 경계 찾기 ──────────────────────────────────
s3_cover_start  = content.index("<!-- ════════ §3 cover ════════ -->")
s4_slides_start = content.index("<!-- 4-1 9")
s5_cover_start  = content.index("<!-- ════════ §5 cover ════════ -->")

s3_full       = content[s3_cover_start : s4_slides_start]   # §3 cover + slides 10-15
s4_full       = content[s4_slides_start : s5_cover_start]   # slides 16-18 (no cover)
s3_slides_only = s3_full[s3_full.index("\n<!-- 3-1."):]  # 슬라이드만 (cover 제외)

# ── 2. §4(개발과정) → 새 §3(사업계획) ───────────────
ns3 = s4_full
ns3 = ns3.replace(
    '<span class="pill">04</span><span class="ttl">개발 과정 및 방법</span>',
    '<span class="pill">03</span><span class="ttl">사업·서비스 계획</span>')
ns3 = ns3.replace("<b>16쪽</b>", "<b>10쪽</b>")
ns3 = ns3.replace("<b>17쪽</b>", "<b>11쪽</b>")
ns3 = ns3.replace("<b>18쪽</b>", "<b>12쪽</b>")
ns3 = ns3.replace("pytest 711 가드", "pytest 815 가드")  # 스테일 수정

# ── 3. §3(차별성) → 새 §4(경쟁기술) ────────────────
ns4 = s3_slides_only
ns4 = ns4.replace(
    '<span class="pill">03</span><span class="ttl">기존 서비스와의 차별성</span>',
    '<span class="pill">04</span><span class="ttl">경쟁기술 및 현황</span>')
for old, new in [("15쪽","18쪽"),("14쪽","17쪽"),("13쪽","16쪽"),
                 ("12쪽","15쪽"),("11쪽","14쪽"),("10쪽","13쪽")]:
    ns4 = ns4.replace(f"<b>{old}</b>", f"<b>{new}</b>")

# ── 4. 새 section covers ──────────────────────────
s3_cover = """\
<!-- ════════ §3 cover ════════ -->
<section class="slide section-cover">
  <div class="num">03</div>
  <h1>사업·서비스<br>계획</h1>
  <div class="desc">· AI 협업 4축 통합 개발 (815 회귀 가드 · CI 15 jobs)<br>· 1인 production-grade 품질 지표<br>· 양면 가치사슬 — 시민 ↔ 운영자 ↔ 광고주<br>· 24시간 라이브 데모 · app.allthatai.kr</div>
  <div class="judge"><b>평가 기준:</b> 사업·서비스 계획 (창업) — 개발 방법론, 기술 신뢰성, 가치사슬 및 지속 성장 구조</div>
</section>

"""

s4_cover = """\
<!-- ════════ §4 cover ════════ -->
<section class="slide section-cover">
  <div class="num">04</div>
  <h1>경쟁기술 및<br>현황</h1>
  <div class="desc">· 6대 사회적 가치 IDEA<br>· 4단 차등 보상 자동 시스템<br>· 군중밀집 사고 사전 경고<br>· 버스 시스템 통합<br>· 글로벌 4개 도시 서비스가 충족하지 못한 5개 기준 동시 달성</div>
  <div class="judge"><b>평가 기준:</b> 경쟁기술 및 현황 (제품·서비스 차별화) — 기존 솔루션 대비 독창성 + 기술 우위</div>
</section>

"""

# ── 5. 새 §7 발전방향 슬라이드 ───────────────────────
s7_new = """\
<!-- 7-1 서비스 발전방향 -->
<section class="slide">
  <div class="head">
    <div class="section-num"><span class="pill">07</span><span class="ttl">서비스 발전방향</span></div>
    <div class="compete">글로벌 확장 · 기술 고도화 · 사회적 가치 확산</div>
  </div>
  <div class="body">
    <h1>서비스 발전방향 — 단계별 확장 로드맵</h1>
    <div class="col3">
      <div class="diff-box green">
        <h3>🚀 단기 (2026 H2)</h3>
        <p>· 5호선 PoC 협약 체결<br>· CV 정확도 92% → 96%<br>· 광고 1사 파트너십<br>· Android 앱 스토어 출시<br>· 사회적 가치 1차 정량 인증</p>
      </div>
      <div class="diff-box amber">
        <h3>📈 중기 (2027)</h3>
        <p>· 서울 2·9호선 전체 확장<br>· 부산·대구 협약<br>· BLE 비콘 측위 연동<br>· 시리즈 시드 ₩10억 유치<br>· 도쿄 메트로 파이럿</p>
      </div>
      <div class="diff-box violet">
        <h3>🌏 장기 (2028+)</h3>
        <p>· 동남아 5개 도시 진출<br>· 버스 BRT 글로벌 확장<br>· 엣지 AI 독자 칩 개발<br>· Series A ₩50억<br>· 10개 도시 동시 운영</p>
      </div>
    </div>
    <div class="col2" style="margin-top: 4mm;">
      <div>
        <h2>기술 고도화 로드맵</h2>
        <table>
          <tr><th>영역</th><th>현재</th><th>목표</th></tr>
          <tr><td>CV 정확도</td><td class="num">92%</td><td class="num win">97%</td></tr>
          <tr><td>Latency</td><td class="num">1.2초</td><td class="num win">0.3초</td></tr>
          <tr><td>동시 카메라</td><td class="num">1대</td><td class="num win">32대</td></tr>
          <tr><td>지원 언어</td><td class="num">4개</td><td class="num win">12개</td></tr>
          <tr><td>역사 커버리지</td><td class="num">PoC</td><td class="num win">서울 전 역사</td></tr>
        </table>
      </div>
      <div>
        <h2>사회적 가치 확산</h2>
        <div class="diff-box green">
          <h3>🏛️ 공공 기여</h3>
          <p>· 서울시 교통 빅데이터 포털 연동<br>· 군중밀집 사고 예방 통계 공개<br>· 청각 장애인 앱 무료 제공<br>· Apache 2.0 오픈소스 유지</p>
        </div>
        <div class="diff-box amber" style="margin-top:3mm;">
          <h3>🌱 ESG 3년 목표</h3>
          <p>· CO₂ 절감 1,000t/년 (3년차)<br>· 교통약자 접근성 개선 측정<br>· 무임승차 감소 → 운영 수익 환원</p>
        </div>
      </div>
    </div>
  </div>
  <div class="foot"><span>2026 Q2 대회 → 2028 글로벌 10개 도시 · 사회적 가치 + 기술 고도화 + 시장 확장</span><span class="pgnum"><b>26쪽</b></span></div>
</section>

"""

# ── 6. §7 참고문헌 슬라이드: 26쪽 → 27쪽, 711→815, admin.html 제거 ──────
# 이 작업은 §5 cover 이후 구간에서만 처리

after_s5 = content[s5_cover_start:]
after_s5 = after_s5.replace('<b>26쪽</b>', '<b>27쪽</b>')
after_s5 = after_s5.replace('pytest 711 가드', 'pytest 815 가드')
after_s5 = after_s5.replace(
    'frontend/operator_web/{realbev,index,bus,ad_pricing}.html + admin.html',
    'frontend/operator_web/{realbev,index,bus,ad_pricing}.html')

# §7 슬라이드 시작 위치에 발전방향 삽입
s7_orig_marker = '<!-- 7-1 기술 스택 + 출처 -->'
after_s5 = after_s5.replace(s7_orig_marker, s7_new + s7_orig_marker)

# ── 7. 조합 ───────────────────────────────────────
new_middle = s3_cover + ns3 + s4_cover + ns4

before_s3 = content[:s3_cover_start]
new_content = before_s3 + new_middle + after_s5

# ── 8. 폰트 CDN 삽입 ─────────────────────────────
font_link = '''\
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css">
'''
new_content = new_content.replace(
    '<title>MetroEyes 상세기획서',
    font_link + '<title>MetroEyes 상세기획서')

# ── 9. CSS 수정: 페이지 합계 26→27, 스크린 overflow ──
new_content = new_content.replace(
    ".foot .pgnum::after { content: ' / 26';",
    ".foot .pgnum::after { content: ' / 27';")
# 스크린에서 overflow 보임
screen_css = "\n@media screen { .slide { overflow: visible; } .body { overflow: visible; } }\n"
new_content = new_content.replace(
    "@media print { body { background: #fff; }",
    screen_css + "@media print { body { background: #fff; }")

# ── 10. HUD 텍스트 업데이트 ───────────────────────
new_content = new_content.replace(
    "📄 30 슬라이드 · PPT 정식 7항목 · A4 가로 · <b>Ctrl+P</b> PDF 저장 (배경 그래픽 ✓)",
    "📄 33 슬라이드 · PPT 정식 7항목 (템플릿 정렬 완료) · A4 가로 · <b>Ctrl+P</b> PDF 저장 (배경 그래픽 ✓)")

# ── 저장 ────────────────────────────────────────
SRC.write_text(new_content, encoding="utf-8")
print(f"완료: {len(new_content):,} chars (원본 대비 +{len(new_content)-len(content):,})")

# 검증
for check in ["폰트 CDN", "사업·서비스 계획", "경쟁기술 및 현황", "서비스 발전방향", "26쪽</b>", "27쪽</b>"]:
    found = check in new_content
    label = "폰트 CDN" if check == "폰트 CDN" else check
    print(f"  {'✓' if found else '✗'} {label} : {'있음' if found else '없음'}")
