"""Tests for the ``battwin[sim]`` Thevenin adapter.

The suite skips cleanly when pybamm is not installed (the same pattern as
``test_shacl.py``); the synthetic ECM-PS below is a tiny 2-RC document whose
flat parameters make the expected behavior easy to reason about.
"""

from __future__ import annotations

import importlib.util

import pytest

from battwin.ecm import ecm_ps_problems
from battwin.sim import build_thevenin, load_table, run_experiment

pybamm_missing = importlib.util.find_spec("pybamm") is None
needs_pybamm = pytest.mark.skipif(pybamm_missing, reason="sim tests need battwin[sim] (pybamm)")

SOCS = [0.05, 0.2, 0.5, 0.8, 1.0]
TEMPS = [10.0, 25.0, 40.0]


def _rows() -> list[dict]:
    rows = []
    for t in TEMPS:
        for s in SOCS:
            rows.append(
                {
                    "state_of_charge": s,
                    "temperature_degc": t,
                    "ocv_charge_volt": 3.0 + 1.2 * s + 0.01,
                    "ocv_discharge_volt": 3.0 + 1.2 * s - 0.01,
                    "series_resistance_ohm": 0.005,
                    "polarization_resistance_1_ohm": 0.003,
                    "polarization_capacitance_1_farad": 1500.0,
                    "polarization_resistance_2_ohm": 0.001,
                    "polarization_capacitance_2_farad": 60000.0,
                    "hysteresis_decay_rate_dimensionless": 30.0,
                    "entropic_coefficient_volt_per_kelvin": 0.0001,
                }
            )
    return rows


ECM_PS = {
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
        "upper_cutoff_voltage_volt": 4.25,
        "lower_cutoff_voltage_volt": 2.5,
    },
    "parameters": {
        "representation": "lookup",
        "independent_variables": [
            {
                "name": "state_of_charge",
                "unit": "dimensionless",
                "range": {"min": 0.05, "max": 1.0},
            },
            {"name": "temperature_degc", "unit": "degreeCelsius", "values": TEMPS},
        ],
        "columns": [
            {"name": "ocv_charge_volt", "unit": "volt", "role": "ocv_charge"},
            {"name": "ocv_discharge_volt", "unit": "volt", "role": "ocv_discharge"},
            {"name": "series_resistance_ohm", "unit": "ohm", "role": "series_resistance"},
            {
                "name": "polarization_resistance_1_ohm",
                "unit": "ohm",
                "role": "polarization_resistance",
                "branch_index": 1,
            },
            {
                "name": "polarization_capacitance_1_farad",
                "unit": "farad",
                "role": "polarization_capacitance",
                "branch_index": 1,
            },
            {
                "name": "polarization_resistance_2_ohm",
                "unit": "ohm",
                "role": "polarization_resistance",
                "branch_index": 2,
            },
            {
                "name": "polarization_capacitance_2_farad",
                "unit": "farad",
                "role": "polarization_capacitance",
                "branch_index": 2,
            },
            {
                "name": "hysteresis_decay_rate_dimensionless",
                "unit": "dimensionless",
                "role": "hysteresis_decay",
            },
            {
                "name": "entropic_coefficient_volt_per_kelvin",
                "unit": "volt_per_kelvin",
                "role": "entropic_coefficient",
            },
        ],
        "table": "synthetic.params.ecm.csv",
    },
}


def test_fixture_is_a_valid_ecm_ps():
    assert ecm_ps_problems(ECM_PS) == []


def test_load_table_accepts_inline_rows():
    doc = {"parameters": {"table": [{"state_of_charge": "0.5", "series_resistance_ohm": "0.005"}]}}
    rows = load_table(doc)
    assert rows == [{"state_of_charge": 0.5, "series_resistance_ohm": 0.005}]


def test_load_table_reads_csv(tmp_path):
    (tmp_path / "t.csv").write_text(
        "state_of_charge,series_resistance_ohm\n0.5,0.005\n", encoding="utf-8"
    )
    rows = load_table({"parameters": {"table": "t.csv"}}, base_dir=tmp_path)
    assert rows[0]["series_resistance_ohm"] == 0.005


def test_build_without_pybamm_raises_actionable_import_error(monkeypatch):
    if not pybamm_missing:
        pytest.skip("pybamm installed; the error path needs it absent")
    with pytest.raises(ImportError, match=r"battwin\[sim\]"):
        build_thevenin(ECM_PS, table=_rows())


@needs_pybamm
def test_build_thevenin_reports_hysteresis_warning():
    build = build_thevenin(ECM_PS, table=_rows())
    assert build.options == {"number of rc elements": 2}
    assert any("hysteresis" in w.lower() for w in build.warnings)


@needs_pybamm
def test_current_axis_is_rejected():
    doc = {
        **ECM_PS,
        "parameters": {
            **ECM_PS["parameters"],
            "independent_variables": ECM_PS["parameters"]["independent_variables"]
            + [{"name": "current_ampere", "unit": "ampere"}],
        },
    }
    with pytest.raises(ValueError, match="current_ampere"):
        build_thevenin(doc, table=_rows())


@needs_pybamm
def test_discharge_experiment_runs_and_signs_follow_bdf():
    build = build_thevenin(ECM_PS, table=_rows(), initial_soc=1.0)
    result = run_experiment(build, ["Discharge at 1C for 10 minutes"], period_s=30.0)
    voltage = result["voltage_volt"]
    assert len(voltage) > 2
    assert voltage[-1] < voltage[0]  # discharging: voltage falls
    # BDF sign convention: discharge current is negative
    assert all(i <= 0 for i in result["current_ampere"][1:])
    soc = result["state_of_charge"]
    assert soc[-1] < soc[0] < 1.001
