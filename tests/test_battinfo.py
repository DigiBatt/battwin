"""Tests for seeding envelopes from BattINFO records.

The fixture record mirrors the real battery-genome registry export for the
Molicel INR2170-P45B (fetched 2026-08-10): sparse ``specs``, ``"unknown"``
placeholder strings, identity split between ``metadata`` and the
``battinfo_records.*.product`` block. No test performs network I/O -- the
record loader is injected.
"""

from __future__ import annotations

import json

import pytest

from battwin import cli, envelope_from_battinfo, validate_dict
from battwin.battinfo import fetch_battinfo_record

P45B_IRI = "https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r"

P45B_RECORD = {
    "@id": "https://w3id.org/battinfo/cell-type/ycek-4qa3-d4v3-rm6r",
    "@type": "CellType",
    "title": "Molicel INR2170-P45B",
    "identifier": "ycek-4qa3-d4v3-rm6r",
    "metadata": {
        "chemistry": "unknown",
        "format": "unknown",
        "manufacturer": "Molicel",
        "model": "INR2170-P45B",
    },
    "battinfo_records": {
        "cell_type": {
            "product": {
                "cellFormat": "unknown",
                "chemistry": "unknown",
                "manufacturer": {"name": "Molicel", "type": "Organization"},
                "model": "INR2170-P45B",
                "name": "Molicel INR2170-P45B",
            },
            "specs": {},
        }
    },
    "distributions": [],
}


def _fetch_p45b(iri: str) -> dict:
    assert iri == P45B_IRI
    return json.loads(json.dumps(P45B_RECORD))  # deep copy: callers must not mutate the fixture


def test_seeds_identity_and_spec_reference():
    envelope = envelope_from_battinfo(P45B_IRI, fetch=_fetch_p45b)
    assert envelope.identity.label == "Molicel INR2170-P45B"
    assert envelope.identity.manufacturer == "Molicel"
    assert envelope.identity.model == "INR2170-P45B"
    assert envelope.specification is not None
    assert envelope.specification.battinfo_record == P45B_IRI


def test_unknown_placeholders_become_absent_fields():
    envelope = envelope_from_battinfo(P45B_IRI, fetch=_fetch_p45b)
    assert envelope.specification is not None
    assert envelope.specification.chemistry is None
    assert envelope.specification.form_factor is None
    assert envelope.specification.nominal_capacity_ah is None


def test_seeded_envelope_is_valid():
    envelope = envelope_from_battinfo(P45B_IRI, fetch=_fetch_p45b)
    assert validate_dict(envelope.to_dict()) == []


def test_label_and_chemistry_overrides_win():
    envelope = envelope_from_battinfo(
        P45B_IRI, label="Bench P45B #1", chemistry="NMC", fetch=_fetch_p45b
    )
    assert envelope.identity.label == "Bench P45B #1"
    assert envelope.specification is not None
    assert envelope.specification.chemistry == "NMC"
    # slug maps every non-alphanumeric char to "-" (same rule as new_envelope)
    assert envelope.id.startswith("urn:bte:bench-p45b--1:")


def test_specs_fields_seed_capacity_and_voltage():
    record = json.loads(json.dumps(P45B_RECORD))
    record["battinfo_records"]["cell_type"]["specs"] = {
        "nominal_capacity_ah": 4.5,
        "nominal_voltage_volt": 3.6,
    }
    envelope = envelope_from_battinfo(P45B_IRI, fetch=lambda iri: record)
    assert envelope.specification is not None
    assert envelope.specification.nominal_capacity_ah == 4.5
    assert envelope.specification.nominal_voltage_volt == 3.6


def test_minimal_record_falls_back_to_iri_tail_label():
    envelope = envelope_from_battinfo("https://example.org/records/abc-123", fetch=lambda iri: {})
    assert envelope.identity.label == "abc-123"
    assert validate_dict(envelope.to_dict()) == []


def test_fetch_rejects_non_http_iri():
    with pytest.raises(ValueError, match="HTTP"):
        fetch_battinfo_record("urn:not:a:url")


def test_cli_init_from_battinfo(tmp_path, capsys, monkeypatch):
    import battwin.battinfo as battinfo_module

    monkeypatch.setattr(battinfo_module, "fetch_battinfo_record", _fetch_p45b)
    out = tmp_path / "p45b.twin.json"
    assert cli.main(["init", "--from-battinfo", P45B_IRI, "-o", str(out)]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["identity"]["label"] == "Molicel INR2170-P45B"
    assert doc["specification"]["battinfo_record"] == P45B_IRI
    assert validate_dict(doc) == []


def test_cli_init_requires_label_or_iri(tmp_path, capsys):
    assert cli.main(["init", "-o", str(tmp_path / "x.twin.json")]) == 2
    assert "--label is required" in capsys.readouterr().err


def test_cli_init_network_failure_exits_cleanly(tmp_path, capsys, monkeypatch):
    import urllib.error

    import battwin.battinfo as battinfo_module

    def boom(iri: str) -> dict:
        raise urllib.error.URLError("name or service not known")

    monkeypatch.setattr(battinfo_module, "fetch_battinfo_record", boom)
    assert cli.main(["init", "--from-battinfo", P45B_IRI, "-o", str(tmp_path / "x.json")]) == 2
    assert "error:" in capsys.readouterr().err
