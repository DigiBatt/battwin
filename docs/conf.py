"""Sphinx configuration for the battwin documentation site."""

from __future__ import annotations

from datetime import date
from importlib.metadata import version as _pkg_version
from pathlib import Path

_DOCS = Path(__file__).resolve().parent
_ROOT = _DOCS.parent
_GENERATED = _DOCS / "_generated"
_BLOB = "https://github.com/DigiBatt/battwin/blob/main/"

project = "battwin"
author = "Simon Clark and contributors"
copyright = f"{date.today().year}, the battwin contributors. Apache-2.0"
release = _pkg_version("battwin")
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxcontrib.autodoc_pydantic",
]

exclude_patterns = ["_build", "_generated", "Thumbs.db", ".DS_Store"]

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist"]
myst_heading_anchors = 4

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"

autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_field_list_validators = False
autodoc_pydantic_model_member_order = "bysource"

html_theme = "pydata_sphinx_theme"
html_title = "battwin"
html_theme_options = {
    "github_url": "https://github.com/DigiBatt/battwin",
    "icon_links": [
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/battwin/",
            "icon": "fa-brands fa-python",
        },
    ],
    "navbar_align": "left",
    "logo": {"text": "battwin"},
    "footer_start": ["copyright"],
    "footer_end": [],
}
html_context = {
    "github_user": "DigiBatt",
    "github_repo": "battwin",
    "github_version": "main",
    "doc_path": "docs",
}

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True


def _rewrite_repo_links(text: str) -> str:
    """Point repo-relative links in root documents at the site or GitHub.

    The generated copies live in ``docs/_generated`` and are included by pages
    under ``docs/reference``, so page links are written relative to that
    directory; source-tree targets go to GitHub.
    """
    text = text.replace("](SPEC.md)", "](specification.md)")
    text = text.replace("](CHANGELOG.md)", "](changelog.md)")
    for target in ("examples/", "src/", "tests/", "LICENSE", "NOTICE", "README.md"):
        text = text.replace(f"]({target}", f"]({_BLOB}{target}")
    return text


def _generate_includes() -> None:
    """Copy the canonical root documents into the docs tree at build time.

    SPEC.md, CHANGELOG.md, and CONTRIBUTING.md stay the single source of
    truth at the repository root; the site renders these generated,
    link-rewritten copies (gitignored) via ``include`` directives.
    """
    _GENERATED.mkdir(exist_ok=True)

    spec = _rewrite_repo_links((_ROOT / "SPEC.md").read_text(encoding="utf-8"))
    note = (
        "\n```{admonition} Canonical source\n:class: note\n\n"
        "This page is rendered from "
        "[`SPEC.md`](https://github.com/DigiBatt/battwin/blob/main/SPEC.md) "
        "in the repository, which is the normative document.\n```\n"
    )
    head, _, body = spec.partition("\n")
    (_GENERATED / "spec.md").write_text(head + "\n" + note + body, encoding="utf-8")

    for src, dest in (("CHANGELOG.md", "changelog.md"), ("CONTRIBUTING.md", "contributing.md")):
        text = _rewrite_repo_links((_ROOT / src).read_text(encoding="utf-8"))
        (_GENERATED / dest).write_text(text, encoding="utf-8")


_generate_includes()
