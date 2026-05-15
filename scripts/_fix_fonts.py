"""HTML 인라인 폰트 사이즈를 가독성 기준으로 올림. 9~11px의 너무 작은 글자만 타겟."""
import re, glob, os, sys
sys.stdout.reconfigure(encoding='utf-8')

# (old → new) — 작은 폰트만, 큰 폰트는 그대로
RULES = [
    (re.compile(r'font-size:\s*9px\b'),  'font-size: 11px'),
    (re.compile(r'font-size:\s*10px\b'), 'font-size: 12px'),
    (re.compile(r'font-size:\s*11px\b'), 'font-size: 13px'),
    (re.compile(r'font-size:\s*12px\b'), 'font-size: 14px'),
]

SKIP_FILES = ('onepager.html',)  # mm 단위 인쇄 전용

total = 0
files_changed = []
for f in glob.glob('frontend/**/*.html', recursive=True):
    base = os.path.basename(f)
    if base in SKIP_FILES: continue
    with open(f, 'r', encoding='utf-8') as fh:
        txt = fh.read()
    orig = txt
    cnt = 0
    for pat, rep in RULES:
        new, n = pat.subn(rep, txt)
        txt = new; cnt += n
    if txt != orig:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(txt)
        files_changed.append((f, cnt))
        total += cnt

print(f'Total replacements: {total}')
for f, cnt in files_changed:
    print(f'  {f}: {cnt}')
