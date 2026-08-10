# Contributing

## Development setup

1. Create and activate a virtual environment.
2. Install development dependencies:

```bash
pip install -e ".[dev,shacl]"
```

## Common commands

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

## Documentation

The docs site is built with Sphinx (MyST Markdown, pydata theme), structured along [Diátaxis](https://diataxis.fr/) lines (tutorials / how-to / reference / explanation), and deployed to GitHub Pages on every push to `main`. `SPEC.md`, `CHANGELOG.md`, and this file are rendered into the site from the repository root, so edit them here, not under `docs/`. To build locally:

```bash
pip install -e ".[docs]"
sphinx-build -W -b html docs site
```

## Pull request checklist

- Add or update tests for behavior changes.
- Keep public APIs backwards compatible unless explicitly planned.
- Update `CHANGELOG.md` for user-visible changes.
