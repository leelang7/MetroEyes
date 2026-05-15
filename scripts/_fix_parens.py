"""앞선 _strip_cycle.py가 빈 괄호 `()`를 무차별 제거해서 JS IIFE가 깨졌음.
이걸 다시 복원."""
import re, glob

total = 0
for f in glob.glob('frontend/**/*.html', recursive=True):
    with open(f, 'r', encoding='utf-8') as fh: txt = fh.read()
    orig = txt
    # 1) `function{` 또는 `function {` → `function() {`
    txt = re.sub(r'function\s*\{', 'function() {', txt)
    # 2) `=>` 없이 단독 `function(...)`도 OK. 위 1)만 적용하면 충분.
    # 3) `onclick="window.print"` (메서드 호출이 인자 없이 호출인 경우) → `onclick="window.print()"`
    txt = re.sub(r'onclick="window\.print"', 'onclick="window.print()"', txt)
    txt = re.sub(r'onclick="window\.location\.reload"', 'onclick="window.location.reload()"', txt)
    # 4) IIFE 종료 `})();` → `})()`가 `});`로 망가졌을 때. ;로 끝나는 짧은 IIFE 패턴만 보수적으로:
    #    `(function() { ... });`  →  `(function() { ... })();`
    #    매칭이 위험할 수 있어 multiline 패턴으로 `(function() {`로 시작하고 짝맞는 `});`로 끝나는 부분만.
    #    여기선 단일 라인 IIFE만 패치 (안전).
    txt = re.sub(
        r"\((function\(\)\s*\{[^}]*?\})\);",
        r"(\1)();",
        txt,
    )
    if txt != orig:
        with open(f, 'w', encoding='utf-8') as fh: fh.write(txt)
        print(f'  patched: {f}')
        total += 1
print(f'done: {total} files')
