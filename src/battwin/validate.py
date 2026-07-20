"""Validation of Battery Twin Envelope documents.

Three layers, matching the spec:

1. **JSON Schema** (``battwin/schemas/twin-envelope.schema.json``) — the public,
   language-neutral contract. Anyone can validate an envelope without Python.
2. **Model rules** (pydantic, :mod:`battwin.envelope`) — the reference
   implementation's stricter semantic checks (e.g. a model binding must have
   exactly one of ``source``/``inline``).
3. **SHACL shapes** (``battwin/shapes/twin-envelope.shapes.ttl``, optional) —
   graph-level constraints on the JSON-LD rendering, so envelopes exchanged
   as RDF are checkable too. Requires the ``battwin[shacl]`` extra.

``validate_dict``/``validate_file`` run the first two — plus the
version-declaration rule of SPEC.md §3.1 (a document must declare a
``bte_version`` that defines every field it uses) — and the SHACL layer when
called with ``shacl=True``. They return a flat list of human-readable problem
strings (empty list = valid).
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import ValidationError

from .envelope import _JSONLD_KEYS

SCHEMA_RESOURCE = "twin-envelope.schema.json"
CONTEXT_RESOURCE = "twin-envelope.context.jsonld"
SHAPES_RESOURCE = "twin-envelope.shapes.ttl"

#: Namespaces used to shorten IRIs in SHACL problem strings (mirrors the
#: prefixes bound in the packaged JSON-LD context).
_NAMESPACES = (
    ("bte", "https://w3id.org/battinfo/twin#"),
    ("schema", "https://schema.org/"),
    ("battinfo", "https://w3id.org/battinfo/"),
)

#: StateSnapshot fields introduced by BTE 0.1.1 (SPEC.md §3.5).
_STATE_FIELDS_0_1_1 = ("energy_throughput_kwh", "equivalent_full_cycles")


# --- Format assertions (SPEC.md §5) --------------------------------------
# In JSON Schema 2020-12 ``format`` is an *annotation*: a validator only turns
# it into an assertion when handed a format checker. The packaged schema marks
# ``state.as_of`` / ``provenance.created`` / ``version.timestamp`` as
# ``format: date-time`` and ``identity.battinfo_iri`` as ``format: uri``, so we
# pass a checker to the validator — otherwise a non-Python consumer validating
# against the contract would reject a malformed datetime or IRI that we silently
# accept.
#
# ``jsonschema`` only ships checkers for a few stdlib-checkable formats;
# ``date-time`` and ``uri`` require the optional ``jsonschema[format]`` extra
# (rfc3339-validator / rfc3987), which battwin does NOT depend on. To keep the
# assertion dependency-free we register lightweight fallbacks for exactly those
# two formats, and only where the environment has not already supplied a
# stricter checker (an install that DOES have ``jsonschema[format]`` keeps its
# native, canonical ones).

_RFC3339_DATETIME = re.compile(
    r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
    r"T([01]\d|2[0-3]):[0-5]\d:([0-5]\d|60)(\.\d+)?"
    r"(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)


def _is_rfc3339_datetime(value: object) -> bool:
    """Whether ``value`` is a well-formed RFC 3339 date-time (schema ``date-time``).

    Non-strings defer to the schema's ``type`` keyword. Canonical UTC-'Z'
    narrowing (SPEC.md §4) is the model and SHACL layers' job, not this one:
    here we only reject strings that are not date-times at all.
    """
    if not isinstance(value, str):
        return True
    if _RFC3339_DATETIME.match(value) is None:
        return False
    try:  # reject impossible calendar dates, e.g. 2026-02-30
        datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _is_uri(value: object) -> bool:
    """Whether ``value`` is an absolute URI/IRI (schema ``uri``): a scheme is
    required and no whitespace is allowed. Non-strings defer to ``type``."""
    if not isinstance(value, str):
        return True
    if re.match(r"^[A-Za-z][A-Za-z0-9+.\-]*:", value) is None:
        return False
    return re.search(r"\s", value) is None


def _build_format_checker() -> jsonschema.FormatChecker:
    """Draft 2020-12 checker plus dependency-free ``date-time``/``uri`` fallbacks."""
    checker = jsonschema.FormatChecker()
    checker.checkers = dict(jsonschema.Draft202012Validator.FORMAT_CHECKER.checkers)
    if "date-time" not in checker.checkers:
        checker.checks("date-time")(_is_rfc3339_datetime)
    if "uri" not in checker.checkers:
        checker.checks("uri")(_is_uri)
    return checker


#: Format checker passed to the schema validator so ``format`` is asserted, not
#: merely annotated (see the note above).
_FORMAT_CHECKER = _build_format_checker()


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Return the packaged BTE JSON Schema."""
    text = (resources.files("battwin") / "schemas" / SCHEMA_RESOURCE).read_text("utf-8")
    return json.loads(text)


@lru_cache(maxsize=1)
def load_context() -> dict[str, Any]:
    """Return the packaged BTE JSON-LD context (the value of ``@context``)."""
    text = (resources.files("battwin") / "context" / CONTEXT_RESOURCE).read_text("utf-8")
    return json.loads(text)["@context"]


@lru_cache(maxsize=1)
def load_shapes() -> str:
    """Return the packaged BTE SHACL shapes as Turtle text."""
    return (resources.files("battwin") / "shapes" / SHAPES_RESOURCE).read_text("utf-8")


def _shorten(term: Any) -> str:
    """Compact a full IRI to a ``prefix:name`` form for problem strings."""
    text = str(term)
    for prefix, namespace in _NAMESPACES:
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace) :]}"
    return text


def shacl_problems(doc: dict[str, Any]) -> list[str]:
    """Validate the JSON-LD rendering of ``doc`` against the packaged shapes.

    Plain-JSON documents are wrapped with the packaged ``@context`` (and
    ``@id``/``@type``) first; documents that already carry ``@context`` are
    parsed as-is. Returns problems formatted like the other layers, prefixed
    ``shacl:``. Requires the optional dependency **pyshacl**.
    """
    try:
        import pyshacl
        from rdflib import Graph, URIRef
        from rdflib.namespace import RDF, SH
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(
            "SHACL validation requires the optional dependency pyshacl; "
            'install it with: pip install "battwin[shacl]"'
        ) from exc

    if "@context" in doc:
        jsonld = doc
    else:
        jsonld = {"@context": load_context(), "@type": "TwinEnvelope", **doc}
        if isinstance(doc.get("id"), str):
            jsonld["@id"] = doc["id"]

    data_graph = Graph()
    data_graph.parse(data=json.dumps(jsonld), format="json-ld")
    shapes_graph = Graph()
    shapes_graph.parse(data=load_shapes(), format="turtle")

    conforms, report, _ = pyshacl.validate(data_graph, shacl_graph=shapes_graph)
    if conforms:
        return []

    problems: list[str] = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        path = report.value(result, SH.resultPath)
        focus = report.value(result, SH.focusNode)
        where = _shorten(path) if isinstance(path, URIRef) else _shorten(focus)
        message = report.value(result, SH.resultMessage) or "constraint violated"
        problems.append(f"shacl: {where}: {message}")
    return sorted(problems)


def validate_dict(doc: dict[str, Any], *, shacl: bool = False) -> list[str]:
    """Validate a parsed envelope document; returns problems (empty = valid).

    With ``shacl=True`` the packaged SHACL shapes are also run against the
    JSON-LD rendering (requires the ``battwin[shacl]`` extra).
    """
    plain = {k: v for k, v in doc.items() if k not in _JSONLD_KEYS}
    if "id" not in plain and "@id" in doc:
        plain["id"] = doc["@id"]

    problems: list[str] = []

    validator = jsonschema.Draft202012Validator(load_schema(), format_checker=_FORMAT_CHECKER)
    for error in sorted(validator.iter_errors(plain), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in error.absolute_path) or "<root>"
        problems.append(f"schema: {where}: {error.message}")

    from .io import from_dict  # local import to avoid a module cycle

    try:
        from_dict(doc)
    except ValidationError as exc:
        for err in exc.errors():
            where = "/".join(str(p) for p in err["loc"]) or "<root>"
            problems.append(f"model: {where}: {err['msg']}")
    except ValueError as exc:
        problems.append(f"model: <root>: {exc}")

    problems.extend(_version_declaration_problems(plain))

    if shacl:
        problems.extend(shacl_problems(doc))

    return problems


def _version_declaration_problems(plain: dict[str, Any]) -> list[str]:
    """SPEC.md §3.1: a document MUST declare a ``bte_version`` >= the earliest
    specification version that defines every field it uses."""
    if plain.get("bte_version") != "0.1.0":
        return []
    problems: list[str] = []
    if "extensions" in plain:
        problems.append(
            "version: extensions: field requires bte_version >= 0.1.1 (document declares 0.1.0)"
        )
    snapshots: list[tuple[str, Any]] = [("state", plain.get("state"))]
    history = plain.get("state_history")
    if isinstance(history, list):
        snapshots.extend((f"state_history/{i}", snap) for i, snap in enumerate(history))
    for where, snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        for field in _STATE_FIELDS_0_1_1:
            if field in snapshot:
                problems.append(
                    f"version: {where}/{field}: field requires bte_version >= 0.1.1 "
                    "(document declares 0.1.0)"
                )
    return problems


def validate_file(path: str | Path, *, shacl: bool = False) -> list[str]:
    """Validate an envelope file; returns problems (empty = valid).

    With ``shacl=True`` the packaged SHACL shapes are also run (requires the
    ``battwin[shacl]`` extra).
    """
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"json: not parseable: {exc}"]
    if not isinstance(doc, dict):
        return ["json: expected a JSON object at the top level"]
    return validate_dict(doc, shacl=shacl)
