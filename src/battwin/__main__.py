"""Module entry point so ``python -m battwin ...`` works like the console script."""

from .cli import main

raise SystemExit(main())
