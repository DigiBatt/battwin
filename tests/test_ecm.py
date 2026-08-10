"""Tests for the packaged ECM-PS schema and its validation helpers."""

from __future__ import annotations

import json

import pytest

from battwin.ecm import ecm_ps_problems, load_ecm_schema, validate_ecm_ps_file

MINIMAL_ECM_PS = {
    "ecm_ps_version": "0.1",
    "profile": "https://w3id.org/emmo/domain/equivalent-circuit-model#TheveninEquivalentCircuitModel",
    "topology": {"rc_branches": 2, "hysteresis": "one-state", "entropic": True, "diffusion": False},
    "conventions": {
        "current_sign": "positive_charge",
        "soc_definition": "fraction_0_1",
        "temperature_reference": "cell surface",
    },
    "cell": {
        "nominal_capacity_ampere_hour": 4.5,
        "upper_cutoff_voltage_volt": 4.2,
        "lower_cutoff_voltage_volt": 2.5,
        "battinfo_record": "https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r",
    },
    "parameters": {
        "representation": "lookup",
        "independent_variables": [
            {"name": "state_of_charge", "unit": "dimensionless", "range": {"min": 0.0, "max": 1.0}},
            {"name": "temperature_degc", "unit": "degreeCelsius", "values": [10, 25, 40, 60]},
        ],
        "columns": [
            {
                "name": "series_resistance_ohm",
                "unit": "ohm",
                "role": "series_resistance",
                "pybamm_name": "R0 [Ohm]",
            }
        ],
        "table": "params.ecm.csv",
    },
}


def test_packaged_schema_loads_and_has_expected_id():
    schema = load_ecm_schema()
    assert schema["$id"].endswith("/schema/ecm-params/0.1")
    assert "parameters" in schema["required"]


def test_minimal_document_is_valid():
    assert ecm_ps_problems(MINIMAL_ECM_PS) == []


def test_missing_required_section_is_reported():
    doc = {k: v for k, v in MINIMAL_ECM_PS.items() if k != "conventions"}
    problems = ecm_ps_problems(doc)
    assert problems and any("conventions" in p for p in problems)


def test_bad_axis_name_is_reported():
    doc = json.loads(json.dumps(MINIMAL_ECM_PS))
    doc["parameters"]["independent_variables"][0]["name"] = "soc_percent"
    problems = ecm_ps_problems(doc)
    assert any("independent_variables" in p for p in problems)


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
