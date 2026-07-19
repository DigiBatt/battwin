"""Third validation layer: SHACL shapes over the JSON-LD rendering.

The pyshacl-requiring tests are skipped when the ``battwin[shacl]`` extra is
not installed, so the core suite stays green without it.
"""

import builtins
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from battwin import load, load_shapes, shacl_problems, validate_dict
from battwin.cli import main

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "cr2032.twin.json"

HAS_PYSHACL = importlib.util.find_spec("pyshacl") is not None
needs_pyshacl = pytest.mark.skipif(not HAS_PYSHACL, reason="requires the battwin[shacl] extra")


def _example_doc() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_shapes_are_packaged() -> None:
    text = load_shapes()
    assert "sh:NodeShape" in text
    assert "bte:TwinEnvelopeShape" in text


@needs_pyshacl
def test_shapes_parse_as_turtle() -> None:
    from rdflib import Graph

    graph = Graph()
    graph.parse(data=load_shapes(), format="turtle")
    assert len(graph) > 0


@needs_pyshacl
def test_example_conforms() -> None:
    assert shacl_problems(_example_doc()) == []


@needs_pyshacl
def test_jsonld_rendering_conforms() -> None:
    assert shacl_problems(load(EXAMPLE).to_jsonld()) == []


@needs_pyshacl
def test_soc_out_of_range_reported() -> None:
    doc = _example_doc()
    doc["state"]["state_of_charge"] = 1.5
    problems = shacl_problems(doc)
    assert any(p.startswith("shacl:") and "stateOfCharge" in p for p in problems)


@needs_pyshacl
def test_negative_throughput_reported() -> None:
    doc = _example_doc()
    doc["state"]["energy_throughput_kwh"] = -2
    problems = shacl_problems(doc)
    assert any(p.startswith("shacl:") and "energyThroughputKilowattHour" in p for p in problems)


@needs_pyshacl
def test_wrong_datetime_type_reported() -> None:
    doc = _example_doc()
    doc["state"]["as_of"] = 20260707  # a number, not a schema:DateTime string
    problems = shacl_problems(doc)
    assert any(p.startswith("shacl:") and "asOf" in p for p in problems)


@needs_pyshacl
def test_non_canonical_datetime_reported() -> None:
    doc = _example_doc()
    doc["state"]["as_of"] = "2026-07-07T12:00:00+02:00"  # offset, not canonical 'Z'
    problems = shacl_problems(doc)
    assert any(p.startswith("shacl:") and "RFC 3339" in p for p in problems)


@needs_pyshacl
def test_missing_identity_name_reported() -> None:
    doc = _example_doc()
    del doc["identity"]["label"]
    problems = shacl_problems(doc)
    assert any(p.startswith("shacl:") and "schema:name" in p for p in problems)


@needs_pyshacl
def test_validate_dict_shacl_keyword() -> None:
    doc = _example_doc()
    doc["state"]["state_of_charge"] = 1.5
    without = validate_dict(doc)
    with_shacl = validate_dict(copy.deepcopy(doc), shacl=True)
    assert not any(p.startswith("shacl:") for p in without)
    assert any(p.startswith("shacl:") for p in with_shacl)


def test_missing_pyshacl_gives_helpful_error(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pyshacl" or name.startswith("pyshacl."):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match=r"battwin\[shacl\]"):
        shacl_problems(_example_doc())


@needs_pyshacl
def test_cli_validate_shacl_ok(capsys) -> None:
    assert main(["validate", "--shacl", str(EXAMPLE)]) == 0
    assert "ok" in capsys.readouterr().out


@needs_pyshacl
def test_cli_validate_shacl_reports_problems(tmp_path: Path, capsys) -> None:
    doc = _example_doc()
    doc["state"]["state_of_charge"] = 1.5
    bad = tmp_path / "bad.twin.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")

    assert main(["validate", "--shacl", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "INVALID" in out
    assert "shacl:" in out


def test_cli_shacl_without_extra_is_a_clean_error(monkeypatch, capsys) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pyshacl" or name.startswith("pyshacl."):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert main(["validate", "--shacl", str(EXAMPLE)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "battwin[shacl]" in err
