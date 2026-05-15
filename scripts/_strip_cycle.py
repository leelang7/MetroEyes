"""사이클/회귀 가드 내부 지표 노출 제거 — 단순 문자열 치환만 사용 (정규식 X, () 안전)."""
import re, glob

# 1) 사이클 카운트 노출
CYCLE_SUBS = [
    ('(D-1, 541+ 사이클)', '(자동 사이클 운영)'),
    ('D-1, 541+ 사이클', '자동 사이클 운영'),
    ('· v6.15 / 543 사이클 · 844 가드', ''),
    ('v6.15 / 543 사이클 · 844 가드', ''),
    (' · 543 사이클', ''),
    (' · 540+ 사이클', ''),
    (' · 540 사이클', ''),
    ('540+ 사이클', '자동 회귀 검증'),
    ('540 사이클', '자동 회귀 검증'),
    ('543 사이클', '자동 회귀 검증'),
    ('541+ 사이클', '자동 회귀 검증'),
]

# 2) 회귀 가드 카운트 노출
GUARD_SUBS = [
    ('844 회귀 가드', '자동 회귀 검증'),
    ('CI 15 jobs · 844 회귀 가드', 'CI 자동 정합성 · 다중 검증'),
    ('CI 15 jobs/844 회귀 가드', 'CI 자동 정합성 · 다중 검증'),
    ('CI 7 회귀 가드', 'CI 자동 회귀 검증'),
    ('CI 6 회귀 가드', 'CI 자동 회귀 검증'),
    ('회귀 가드 7건', '회귀 검증 자동화'),
    ('회귀 가드 6건', '회귀 검증 자동화'),
]

# 3) 정리된 후 흩어진 누락된 구분자
CLEANUP_SUBS = [
    (' · · ', ' · '),
    (' ·  · ', ' · '),
    ('· )', ')'),
    ('(  ', '('),
    (' . ', '. '),
]

total = 0
for f in glob.glob('frontend/**/*.html', recursive=True):
    with open(f, 'r', encoding='utf-8') as fh: txt = fh.read()
    orig = txt
    for old, new in CYCLE_SUBS + GUARD_SUBS + CLEANUP_SUBS:
        txt = txt.replace(old, new)
    if txt != orig:
        with open(f, 'w', encoding='utf-8') as fh: fh.write(txt)
        print(f'  patched: {f}')
        total += 1
print(f'done: {total} files')
