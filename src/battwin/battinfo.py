"""Seed a Battery Twin Envelope from a BattINFO registry record.

``envelope_from_battinfo`` dereferences a cell-spec IRI (e.g.
``https://w3id.org/battinfo/spec/<id>``), reads the identity facts out of the
returned record, and scaffolds a valid envelope whose ``specification``
references the record by IRI -- the envelope points at the registry, it does
not copy the record in.

Standard library only, by design: fetching a record is one HTTPS GET
returning JSON, so twinning a cell from its IRI works on a bare
``pip install battwin``. (The heavier ``[data]`` extra is for tabular data,
not for this.)

The record shapes handled here follow the battery-genome registry exports:
identity facts are looked up in ``metadata`` first, then in the
``battinfo_records.*.product`` block; the literal string ``"unknown"`` is
treated as absent, so a sparse record seeds a sparse (but valid) envelope
rather than one full of placeholder values.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import Any

from .envelope import (
    Identity,
    Provenance,
    Specification,
    TwinEnvelope,
    VersionInfo,
    _version,
)

__all__ = ["envelope_from_battinfo", "fetch_battinfo_record"]

_TIMEOUT_S = 30.0


def fetch_battinfo_record(iri: str, *, timeout_s: float = _TIMEOUT_S) -> dict[str, Any]:
    """Dereference ``iri`` (following redirects) and return the JSON record.

    Sends ``Accept: application/json``; w3id.org IRIs 303-redirect to the
    registry, which urllib follows. Raises ``ValueError`` for a non-HTTP IRI
    or a non-object payload, and lets network errors (``urllib.error.URLError``,
    an ``OSError`` subclass) propagate for the caller to surface.
    """
    if not iri.startswith(("https://", "http://")):
        raise ValueError(f"not an HTTP(S) IRI: {iri!r}")
    request = urllib.request.Request(
        iri,
        headers={
            "Accept": "application/json",
            # Some hosts on the redirect chain (w3id.org, CDN fronts) reject
            # the default Python-urllib agent outright with a 403.
            "User-Agent": f"battwin/{_version()}",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        payload = response.read()
    try:
        doc = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{iri}: the response is not JSON ({exc})") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"{iri}: expected a JSON object, got {type(doc).__name__}")
    return doc


def envelope_from_battinfo(
    iri: str,
    *,
    label: str | None = None,
    twin_id: str | None = None,
    chemistry: str | None = None,
    created_by: str | None = None,
    timestamp: datetime | None = None,
    fetch: Callable[[str], dict[str, Any]] | None = None,
) -> TwinEnvelope:
    """Scaffold an envelope for the cell described by a BattINFO record.

    The record is dereferenced and its identity facts (name, manufacturer,
    model, chemistry, capacity/voltage when present) seed ``identity`` and
    ``specification``; ``specification.battinfo_record`` carries the given
    IRI so consumers can re-resolve the source. ``label`` and ``chemistry``
    override what the record says (useful while a record is sparse).
    ``fetch`` injects a record loader for tests (defaults to
    :func:`fetch_battinfo_record`).
    """
    doc = (fetch or fetch_battinfo_record)(iri)
    product = _product_block(doc)
    metadata_raw = doc.get("metadata")
    metadata: dict[str, Any] = metadata_raw if isinstance(metadata_raw, dict) else {}
    specs = _specs_block(doc)

    resolved_label = (
        label
        or _known(doc.get("title"))
        or _known(product.get("name"))
        or iri.rstrip("/").rsplit("/", 1)[-1]
    )
    manufacturer = _known(metadata.get("manufacturer")) or _known(
        _dig(product, "manufacturer", "name")
    )
    model = _known(metadata.get("model")) or _known(product.get("model"))
    chemistry = (
        _known(chemistry) or _known(metadata.get("chemistry")) or _known(product.get("chemistry"))
    )
    form_factor = _known(metadata.get("format")) or _known(product.get("cellFormat"))

    now = timestamp or datetime.now(timezone.utc)
    slug = "".join(c if c.isalnum() else "-" for c in resolved_label.lower()).strip("-")
    return TwinEnvelope(
        id=twin_id or f"urn:bte:{slug}:{date.today().isoformat()}",
        identity=Identity(
            label=resolved_label,
            manufacturer=manufacturer,
            model=model,
        ),
        specification=Specification(
            battinfo_record=iri,
            chemistry=chemistry,
            form_factor=form_factor,
            nominal_capacity_ah=_positive_number(
                specs.get("nominal_capacity_ah") or specs.get("nominal_capacity_ampere_hour")
            ),
            nominal_voltage_volt=_positive_number(
                specs.get("nominal_voltage_volt") or specs.get("nominal_voltage")
            ),
        ),
        provenance=Provenance(created=now, created_by=created_by, tool=f"battwin/{_version()}"),
        version=VersionInfo(timestamp=now),
    )


def _known(value: Any) -> str | None:
    """A non-empty string that is not the registry's ``"unknown"`` placeholder."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text.lower() == "unknown":
        return None
    return text


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if value > 0 else None


def _dig(doc: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(doc, dict):
            return None
        doc = doc.get(key)
    return doc


def _product_block(doc: dict[str, Any]) -> dict[str, Any]:
    """The first ``product`` object under ``battinfo_records``, else ``{}``."""
    records = doc.get("battinfo_records")
    if isinstance(records, dict):
        for record in records.values():
            product = record.get("product") if isinstance(record, dict) else None
            if isinstance(product, dict):
                return product
    return {}


def _specs_block(doc: dict[str, Any]) -> dict[str, Any]:
    """The record's ``specs`` object (registry exports one per record), else ``{}``."""
    records = doc.get("battinfo_records")
    if isinstance(records, dict):
        for record in records.values():
            specs = record.get("specs") if isinstance(record, dict) else None
            if isinstance(specs, dict) and specs:
                return specs
    specs = doc.get("specs")
    return specs if isinstance(specs, dict) else {}
