"""README + 핵심 docs 의 internal markdown link 검증 (cycle 397).

평가위원이 README "For Reviewers" 섹션 링크 클릭 시 404 안 뜨도록 보장.
모든 [text](relative_path) 링크의 target 파일이 실재.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 검사 대상 docs (link 포함)
TARGETS = [
    "README.md",
    "README.en.md",
    "docs/PROPOSAL.md",
    "docs/SUBMISSION_INDEX.md",
    "docs/SUBMISSION_GUIDE.md",
    "docs/RUNBOOK.md",
    "docs/QA_PREPARATION.md",
    "docs/RECORDING_NARRATION.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
]

# markdown link 패턴 [text](relative_or_anchor)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)(?:#[^)]*)?\)")


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _find_broken_links(rel_doc: str) -> list[str]:
    body = _read(rel_doc)
    if not body:
        return []
    doc_dir = (ROOT / rel_doc).parent
    broken = []
    for m in LINK_RE.finditer(body):
        text, target = m.group(1), m.group(2)
        # 외부 URL 건너뛰기
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        # 앵커-only 건너뛰기 (#section)
        if target.startswith("#"):
            continue
        # 절대 경로는 ROOT 기준
        if target.startswith("/"):
            target_path = ROOT / target.lstrip("/")
        else:
            target_path = (doc_dir / target).resolve()
        if not target_path.exists():
            broken.append(f"{rel_doc} → {target} (text: '{text}')")
    return broken


def test_readme_internal_links_resolve() -> None:
    """README.md 내부 링크 모두 실재."""
    broken = _find_broken_links("README.md")
    assert not broken, "README.md broken links:\n  " + "\n  ".join(broken)


def test_readme_en_internal_links_resolve() -> None:
    """README.en.md 내부 링크 모두 실재."""
    broken = _find_broken_links("README.en.md")
    assert not broken, "README.en.md broken links:\n  " + "\n  ".join(broken)


def test_proposal_internal_links_resolve() -> None:
    """docs/PROPOSAL.md 내부 링크 모두 실재."""
    broken = _find_broken_links("docs/PROPOSAL.md")
    assert not broken, "PROPOSAL.md broken links:\n  " + "\n  ".join(broken)


def test_submission_index_links_resolve() -> None:
    """docs/SUBMISSION_INDEX.md 내부 링크 모두 실재."""
    broken = _find_broken_links("docs/SUBMISSION_INDEX.md")
    assert not broken, "SUBMISSION_INDEX.md broken links:\n  " + "\n  ".join(broken)


def test_runbook_internal_links_resolve() -> None:
    """docs/RUNBOOK.md 내부 링크 모두 실재."""
    broken = _find_broken_links("docs/RUNBOOK.md")
    assert not broken, "RUNBOOK.md broken links:\n  " + "\n  ".join(broken)


def test_contributing_internal_links_resolve() -> None:
    """CONTRIBUTING.md 내부 링크 모두 실재."""
    broken = _find_broken_links("CONTRIBUTING.md")
    assert not broken, "CONTRIBUTING.md broken links:\n  " + "\n  ".join(broken)


def test_security_internal_links_resolve() -> None:
    """SECURITY.md 내부 링크 모두 실재."""
    broken = _find_broken_links("SECURITY.md")
    assert not broken, "SECURITY.md broken links:\n  " + "\n  ".join(broken)


def test_all_targets_combined() -> None:
    """전체 target docs 의 모든 link 실재 — 한 번에 fail 명세."""
    all_broken = []
    for t in TARGETS:
        all_broken.extend(_find_broken_links(t))
    assert not all_broken, (
        f"총 {len(all_broken)} 개 broken link 발견:\n  " + "\n  ".join(all_broken)
    )


# === cycle 398 — docs/*.md 전체 자동 sweep ===

def test_all_docs_md_links_resolve() -> None:
    """docs/ 디렉토리의 모든 .md 파일 + 루트 (.md) 의 internal link 일괄 검증."""
    all_broken = []
    # 루트 .md
    for p in ROOT.glob("*.md"):
        rel = p.name
        all_broken.extend(_find_broken_links(rel))
    # docs/*.md 모두
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        for p in docs_dir.glob("*.md"):
            rel = f"docs/{p.name}"
            all_broken.extend(_find_broken_links(rel))
    # 결과
    assert not all_broken, (
        f"docs/*.md + 루트 *.md 에서 총 {len(all_broken)} broken link:\n  " +
        "\n  ".join(all_broken)
    )


def test_changelog_internal_links_resolve() -> None:
    """CHANGELOG.md 가 외부 자료 cross-link 없거나 모두 실재."""
    broken = _find_broken_links("CHANGELOG.md")
    assert not broken, "CHANGELOG.md broken links:\n  " + "\n  ".join(broken)

