"""UI 정리: 모든 페이지의 MetroEyes 브랜드를 hub 링크로 + SubwayBEV 사용자 노출 제거."""
import re, glob

ROOT = "frontend"

# (file → href to hub) — 파일 위치에 따른 상대 경로
HUB_HREF = {
    "frontend/admin.html": "index.html",
    "frontend/pitch.html": "index.html",
    "frontend/demo.html": "index.html",
    "frontend/onepager.html": "index.html",
    "frontend/operator_web/index.html": "../index.html",
    "frontend/operator_web/realbev.html": "../index.html",
    "frontend/operator_web/admin.html": "../index.html",
    "frontend/operator_web/bus.html": "../index.html",
    "frontend/operator_web/ad_pricing.html": "../index.html",
    "frontend/passenger_app/index.html": "../index.html",
    "frontend/passenger_app/onboard.html": "../index.html",
}

# 패턴별 변환 규칙 (정규식)
#  P1: <span class="dot"></span>MetroEyes<small>...</small>  → 링크화
#  P2: <span class="dot"></span>MetroEyes Debug Console      → admin.html (small 없음)
#  P3: <div class="brand">MetroEyes 정책 보고<small>...</small> → pitch.html (다른 layout)
#  P4: <div class="brand" id="brand-text">MetroEyes 통합 시연<small id="brand-sub">... → demo.html
#  P5: <h1>MetroEyes</h1>                                     → onepager.html

def patch_p1(txt, href):
    """<span class="dot"></span>MetroEyes<small>...</small> → 링크화"""
    pat = re.compile(r'(<span class="dot"></span>)MetroEyes(<small>[^<]*</small>)')
    def rep(m):
        return f'<a href="{href}" class="brand-link" title="홈으로 (8페이지 진입 허브)">{m.group(1)}MetroEyes</a>{m.group(2)}'
    return pat.sub(rep, txt)

def patch_p2(txt, href):
    """<span class="dot"></span>MetroEyes Debug Console (small 없음)"""
    pat = re.compile(r'(<span class="dot"></span>)MetroEyes Debug Console')
    return pat.sub(
        lambda m: f'<a href="{href}" class="brand-link" title="홈으로">{m.group(1)}MetroEyes</a><small>Debug Console</small>',
        txt,
    )

def patch_p3(txt, href):
    """<div class="brand">MetroEyes 정책 보고<small>...</small></div>"""
    pat = re.compile(r'<div class="brand">MetroEyes ([^<]+)<small>')
    return pat.sub(
        lambda m: f'<div class="brand"><a href="{href}" class="brand-link" title="홈으로">MetroEyes</a> <span class="brand-suffix">{m.group(1).strip()}</span><small>',
        txt,
    )

def patch_p4(txt, href):
    """<div class="brand" id="brand-text">MetroEyes ...<small id="brand-sub">...</small></div>
    JS가 #brand-text 텍스트를 매번 바꾸므로 a 태그 보존해야 함 → 별도 #brand-suffix span 도입."""
    pat = re.compile(r'<div class="brand" id="brand-text">MetroEyes ([^<]+)<small id="brand-sub">')
    return pat.sub(
        lambda m: f'<div class="brand"><a href="{href}" class="brand-link" title="홈으로">MetroEyes</a> <span id="brand-text">{m.group(1).strip()}</span><small id="brand-sub">',
        txt,
    )

def patch_p5(txt, href):
    """<h1>MetroEyes</h1> in onepager"""
    return txt.replace(
        '<h1>MetroEyes</h1>',
        f'<h1><a href="{href}" class="brand-link no-print" title="홈으로">MetroEyes</a></h1>',
        1,
    )

# SubwayBEV 사용자 노출 부분 제거 (UI strings) — 메모리 규칙에 따라 코드 식별자는 보존
def strip_subwaybev_ui(txt):
    """user-facing 'SubwayBEV — ' / 'SubwayBEV ' 접두사 제거. 코드 식별자(window.SubwayBEV, fileName 등)는 건드리지 않음."""
    # subtitle 패턴: 'SubwayBEV — '
    txt = re.sub(r'SubwayBEV\s*—\s*', '', txt)
    # JS 한글 i18n 객체 내 'SubwayBEV ' (사용자 표시 텍스트)
    return txt

# CSS for .brand-link (모든 페이지 공통) — head 끝에 주입
BRAND_LINK_CSS = """
<style>
/* 브랜드 → 허브 링크 (UI polish) */
.brand-link { color: inherit; text-decoration: none; cursor: pointer; transition: opacity .15s ease, transform .15s ease; }
.brand-link:hover { opacity: .82; transform: translateY(-0.5px); }
.brand-link:active { opacity: .65; }
.brand-suffix { color: var(--muted, #8a8a96); font-weight: 600; margin-left: 4px; }
</style>
"""

def inject_brand_css(txt):
    if 'brand-link' in txt and '.brand-link {' not in txt:
        # </head> 직전에 주입
        return txt.replace('</head>', BRAND_LINK_CSS + '</head>', 1)
    return txt

total_modified = 0
for fpath, href in HUB_HREF.items():
    try:
        with open(fpath, 'r', encoding='utf-8') as fh:
            txt = fh.read()
    except FileNotFoundError:
        print(f'  SKIP (not found): {fpath}')
        continue
    orig = txt
    for p in (patch_p1, patch_p2, patch_p3, patch_p4, patch_p5):
        txt = p(txt, href)
    txt = strip_subwaybev_ui(txt)
    txt = inject_brand_css(txt)
    if txt != orig:
        with open(fpath, 'w', encoding='utf-8') as fh:
            fh.write(txt)
        total_modified += 1
        print(f'  patched: {fpath}')
    else:
        print(f'  no change: {fpath}')

print(f'\ndone: {total_modified} files modified')
