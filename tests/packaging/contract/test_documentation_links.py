"""Check relative Markdown targets and GitHub heading anchors."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.verify import REPO_ROOT

FENCES = re.compile(r"^ {0,3}(`{3,}|~{3,}).*?^ {0,3}\1[ \t]*$", re.M | re.S)
LINKS = re.compile(
    r"\]\((?:<([^>\n]+)>|([^\s)]+))\s*(?:[\"'][^\n]*[\"'])?\)"
    r"|^\s*\[[^\]\n]+\]:\s*<?([^>\s]+)>?"
    r'|\bsrc="([^"]+)"',
    re.M,
)
HEADINGS = re.compile(r"^ {0,3}#{1,6}\s+(.+?)[ \t]*#*[ \t]*$", re.M)


def anchors(path: Path) -> set[str]:
    content = FENCES.sub("", path.read_text(encoding="utf-8"))
    found = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', content))
    counts: dict[str, int] = {}
    for heading in HEADINGS.findall(content):
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        slug = re.sub(r"[^\w -]", "", heading.strip().lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        found.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    return found


def test_relative_markdown_links():
    paths = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md"],
        cwd=REPO_ROOT,
    ).decode("utf-8").split("\0")
    broken = []
    for name in sorted(set(paths) - {""}):
        if name.startswith(("artifacts/", "build/")):
            continue
        source = REPO_ROOT / name
        if not source.is_file():
            continue  # Git can still list an unstaged deletion.
        content = FENCES.sub("", source.read_text(encoding="utf-8"))
        for match in LINKS.finditer(content):
            destination = urlsplit(next(value for value in match.groups() if value))
            if destination.scheme or destination.netloc:
                continue
            target = source.parent / unquote(destination.path) if destination.path else source
            fragment = unquote(destination.fragment)
            if not target.exists() or (
                fragment and target.suffix.lower() == ".md" and fragment not in anchors(target)
            ):
                broken.append(f"{name}: {destination.geturl()}")
    assert not broken, "Broken relative links:\n" + "\n".join(broken)
