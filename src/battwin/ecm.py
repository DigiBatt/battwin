"""ECM Parameter Set (ECM-PS) validation.

An ECM-PS document expresses equivalent-circuit-model parameters in a form
deliberately styled after BPX (Header/Parameterisation/State/Validation
sections, natural-language parameter names with bracketed SI units, values as
constants or interpolated tables), so that ECM-PS reads as the ECM
counterpart of a BPX file even though BPX itself defines no ECM model type.
Semantic grounding lives at spec level: each defined parameter name maps to a
class in the EMMO domain-equivalent-circuit-model ontology, and the Header
may carry a BattINFO record IRI. A twin attaches an ECM-PS through a model
binding whose payload (``inline`` or the document behind ``source``) is the
document itself.

battwin packages the ECM-PS JSON Schema **validation-only**: this module can
check that a payload is a well-formed ECM-PS document, and never evaluates
the model -- execution belongs to PyBaMM/PyBOP and friends (SPEC.md §7).
The schema ``$id`` under the EMMO domain namespace is provisional until the
corresponding w3id redirects are registered.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema

from .validate import _FORMAT_CHECKER

__all__ = ["ecm_ps_problems", "load_ecm_schema", "validate_ecm_ps_file"]

ECM_SCHEMA_RESOURCE = "ecm-params.schema.json"


@lru_cache(maxsize=1)
def load_ecm_schema() -> dict[str, Any]:
    """Return the packaged ECM-PS JSON Schema."""
    text = (resources.files("battwin") / "schemas" / ECM_SCHEMA_RESOURCE).read_text("utf-8")
    return json.loads(text)


def ecm_ps_problems(doc: dict[str, Any]) -> list[str]:
    """Validate a parsed ECM-PS document; returns problems (empty = valid).

    Problem strings follow the envelope validators' format, prefixed
    ``ecm:``. Only schema conformance is checked -- cross-value consistency
    (e.g. that every ``R{i}``/``C{i}`` up to ``Number of RC elements`` is
    present, or that table rows are equally long) is enforced by consumers
    such as :func:`battwin.sim.build_thevenin`.
    """
    validator = jsonschema.Draft202012Validator(load_ecm_schema(), format_checker=_FORMAT_CHECKER)
    problems = []
    for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in error.absolute_path) or "<root>"
        problems.append(f"ecm: {where}: {error.message}")
    return problems


def validate_ecm_ps_file(path: str | Path) -> list[str]:
    """Validate an ECM-PS file; returns problems (empty = valid)."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"json: not parseable: {exc}"]
    if not isinstance(doc, dict):
        return ["json: expected a JSON object at the top level"]
    return ecm_ps_problems(doc)
