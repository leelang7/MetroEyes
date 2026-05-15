"""사이클/회귀 가드 내부 지표 노출 제거 — 공개 페이지에서 중립 표현으로."""
import re, glob

REPLACEMENTS = [
    # "541+ 사이클" / "543 사이클" 등 사이클 카운터
    (re.compile(r"\(D-\d+,\s*\d+\+?\s*사이클\)"), "(자동 사이클 운영 중)"),
    (re.compile(r"D-\d+\s*\d+\+?\s*사이클"), ""),
    (re.compile(r"\d+\+?\s*사이클"), ""),
    # "844 회귀 가드", "CI 15 jobs/844 회귀 가드" 등 가드 카운트
    (re.compile(r"\d+\s*회귀\s*가드"), "자동 회귀 검증"),
    (re.compile(r"/\s*\d+\+?\s*가드"), "/ 자동 회귀 검증"),
    (re.compile(r"\b\d+\s*가드\b"), "자동 회귀 검증"),
]

total = 0
for f in glob.glob('frontend/**/*.html', recursive=True):
    with open(f, 'r', encoding='utf-8') as fh: txt = fh.read()
    orig = txt
    for pat, rep in REPLACEMENTS:
        txt = pat.sub(rep, txt)
    # 정리: 빈 ' / / ' 처럼 짝 안 맞는 부분 정돈
    txt = re.sub(r'·\s*·', '·', txt)
    txt = re.sub(r',\s*,', ',', txt)
    txt = re.sub(r'\(\s*\)', '', txt)
    if txt != orig:
        with open(f, 'w', encoding='utf-8') as fh: fh.write(txt)
        print(f'  patched: {f}')
        total += 1
print(f'done: {total} files')
