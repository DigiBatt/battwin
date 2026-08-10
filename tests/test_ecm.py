"""Tests for the packaged ECM-PS schema and its validation helpers."""

from __future__ import annotations

import json

import pytest

from battwin.ecm import ecm_ps_problems, load_ecm_schema, validate_ecm_ps_file

MINIMAL_ECM_PS = {
    "Header": {
        "ECM-PS version": "0.2",
        "Model": "ECM",
        "Title": "Minimal 1-RC test set",
        "BattINFO record": "https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r",
    },
    "Parameterisation": {
        "Cell": {
            "Nominal cell capacity [A.h]": 4.5,
            "Upper voltage cut-off [V]": 4.2,
            "Lower voltage cut-off [V]": 2.5,
            "Number of RC elements": 1,
        },
        "Circuit": {
            "Open-circuit voltage [V]": {"x": [0.0, 1.0], "y": [3.0, 4.2]},
            "R0 [Ohm]": 0.005,
            "R1 [Ohm]": {
                "x": [0.0, 1.0],
                "y": [280.0, 320.0],
                "z": [[0.003, 0.002], [0.002, 0.001]],
            },
            "C1 [F]": 1500.0,
        },
    },
}


def test_packaged_schema_loads_and_has_expected_id():
    schema = load_ecm_schema()
    assert schema["$id"].endswith("/schema/ecm-params/0.2")
    assert "Parameterisation" in schema["required"]


def test_minimal_document_is_valid():
    assert ecm_ps_problems(MINIMAL_ECM_PS) == []


def test_missing_required_section_is_reported():
    doc = {k: v for k, v in MINIMAL_ECM_PS.items() if k != "Header"}
    problems = ecm_ps_problems(doc)
    assert problems and any("Header" in p for p in problems)


def test_unknown_circuit_parameter_is_rejected():
    doc = json.loads(json.dumps(MINIMAL_ECM_PS))
    doc["Parameterisation"]["Circuit"]["Series resistance [Ohm]"] = 0.005
    problems = ecm_ps_problems(doc)
    assert any("Circuit" in p for p in problems)


def test_expression_string_values_are_rejected():
    doc = json.loads(json.dumps(MINIMAL_ECM_PS))
    doc["Parameterisation"]["Circuit"]["R0 [Ohm]"] = "0.005 * exp(-x)"
    problems = ecm_ps_problems(doc)
    assert any("R0" in p for p in problems)


def test_ocv_or_both_branches_is_required():
    doc = json.loads(json.dumps(MINIMAL_ECM_PS))
    circuit = doc["Parameterisation"]["Circuit"]
    del circuit["Open-circuit voltage [V]"]
    assert ecm_ps_problems(doc)  # no OCV at all
    circuit["Open-circuit voltage on charge [V]"] = {"x": [0.0, 1.0], "y": [3.0, 4.2]}
    assert ecm_ps_problems(doc)  # one branch only
    circuit["Open-circuit voltage on discharge [V]"] = {"x": [0.0, 1.0], "y": [2.9, 4.1]}
    assert ecm_ps_problems(doc) == []  # both branches


def test_problem_strings_carry_the_ecm_prefix_and_a_path():
    problems = ecm_ps_problems({})
    assert problems
    assert all(p.startswith("ecm: ") for p in problems)


@pytest.mark.parametrize("payload", ["not json at all", "[1, 2, 3]"])
def test_validate_file_rejects_non_document_payloads(tmp_path, payload):
    target = tmp_path / "bad.ecm-ps.json"
    target.write_text(payload, encoding="utf-8")
    problems = validate_ecm_ps_file(target)
    assert len(problems) == 1 and problems[0].startswith("json:")


def test_validate_file_accepts_a_valid_document(tmp_path):
    target = tmp_path / "ok.ecm-ps.json"
    target.write_text(json.dumps(MINIMAL_ECM_PS), encoding="utf-8")
    assert validate_ecm_ps_file(target) == []
