"""MkDocs hooks: include selected repo-root files into docs pages.

A docs page can contain a line of the form ``{!! FILENAME !!}``. This hook
replaces it with the content of that file from the repository root, rewriting
repo-relative links so they resolve from the rendered site (source files stay
the single source of truth; the site never duplicates them by hand).
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_BLOB = "https://github.com/DigiBatt/battwin/blob/main/"
_INCLUDE = re.compile(r"\{!!\s*([\w./-]+)\s*!!\}")

# Repo-relative link targets that exist as pages on the site.
_PAGE_LINKS = {
    "SPEC.md": "spec.md",
    "CHANGELOG.md": "changelog.md",
    "CONTRIBUTING.md": "contributing.md",
}

# Repo-relative link targets that only exist on GitHub.
_BLOB_PREFIXES = ("examples/", "src/", "tests/", "LICENSE", "NOTICE", "README.md")


def _rewrite_links(text: str) -> str:
    for target, page in _PAGE_LINKS.items():
        text = text.replace(f"]({target})", f"]({page})")
    for prefix in _BLOB_PREFIXES:
        text = text.replace(f"]({prefix}", f"]({_BLOB}{prefix}")
    return text


def on_page_markdown(markdown: str, page, config, files) -> str:
    def _replace(match: re.Match[str]) -> str:
        source = _ROOT / match.group(1)
        return _rewrite_links(source.read_text(encoding="utf-8"))

    return _INCLUDE.sub(_replace, markdown)
