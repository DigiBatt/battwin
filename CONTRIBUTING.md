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

The docs site is built with MkDocs Material and deployed to GitHub Pages on every push to `main`. To preview locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Pull request checklist

- Add or update tests for behavior changes.
- Keep public APIs backwards compatible unless explicitly planned.
- Update `CHANGELOG.md` for user-visible changes.
