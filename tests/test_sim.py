"""Tests for the ``battwin[sim]`` Thevenin adapter.

The suite skips cleanly when pybamm is not installed (the same pattern as
``test_shacl.py``); the synthetic ECM-PS below is a tiny 2-RC document whose
flat parameters make the expected behavior easy to reason about.
"""

from __future__ import annotations

import importlib.util

import pytest

from battwin.ecm import ecm_ps_problems
from battwin.sim import build_thevenin, run_experiment

pybamm_missing = importlib.util.find_spec("pybamm") is None
needs_pybamm = pytest.mark.skipif(pybamm_missing, reason="sim tests need battwin[sim] (pybamm)")

SOCS = [0.05, 0.2, 0.5, 0.8, 1.0]
TEMPS_K = [283.15, 298.15, 313.15]


def _table2d(value: float) -> dict:
    return {"x": SOCS, "y": TEMPS_K, "z": [[value] * len(SOCS) for _ in TEMPS_K]}


def _ocv_branch(offset: float) -> dict:
    return {"x": SOCS, "y": TEMPS_K, "z": [[3.0 + 1.2 * s + offset for s in SOCS] for _ in TEMPS_K]}


ECM_PS = {
    "Header": {
        "ECM-PS version": "0.2",
        "Model": "ECM",
        "Title": "Synthetic 2-RC test set",
    },
    "Parameterisation": {
        "Cell": {
            "Nominal cell capacity [A.h]": 4.5,
            "Upper voltage cut-off [V]": 4.25,
            "Lower voltage cut-off [V]": 2.5,
            "Number of RC elements": 2,
        },
        "Circuit": {
            "Open-circuit voltage on charge [V]": _ocv_branch(+0.01),
            "Open-circuit voltage on discharge [V]": _ocv_branch(-0.01),
            "Hysteresis decay rate": 30.0,
            "R0 [Ohm]": _table2d(0.005),
            "R1 [Ohm]": _table2d(0.003),
            "C1 [F]": _table2d(1500.0),
            "R2 [Ohm]": 0.001,
            "C2 [F]": {"x": SOCS, "y": [60000.0] * len(SOCS)},
            "Entropic change [V.K-1]": _table2d(0.0001),
        },
    },
}


def test_fixture_is_a_valid_ecm_ps():
    assert ecm_ps_problems(ECM_PS) == []


def test_build_without_pybamm_raises_actionable_import_error(monkeypatch):
    if not pybamm_missing:
        pytest.skip("pybamm installed; the error path needs it absent")
    with pytest.raises(ImportError, match=r"battwin\[sim\]"):
        build_thevenin(ECM_PS)


@needs_pybamm
def test_build_thevenin_reports_hysteresis_warning():
    build = build_thevenin(ECM_PS)
    assert build.options == {"number of rc elements": 2}
    assert any("hysteresis" in w.lower() for w in build.warnings)


@needs_pybamm
def test_expression_string_value_is_rejected():
    doc = {
        **ECM_PS,
        "Parameterisation": {
            **ECM_PS["Parameterisation"],
            "Circuit": {
                **ECM_PS["Parameterisation"]["Circuit"],
                "R0 [Ohm]": "0.005 * exp(-soc)",
            },
        },
    }
    with pytest.raises(ValueError, match="expression strings"):
        build_thevenin(doc)


@needs_pybamm
def test_missing_rc_element_is_reported():
    circuit = {
        k: v
        for k, v in ECM_PS["Parameterisation"]["Circuit"].items()
        if k not in {"R2 [Ohm]", "C2 [F]"}
    }
    doc = {
        **ECM_PS,
        "Parameterisation": {**ECM_PS["Parameterisation"], "Circuit": circuit},
    }
    with pytest.raises(ValueError, match=r"R2 \[Ohm\]"):
        build_thevenin(doc)


@needs_pybamm
def test_discharge_experiment_runs_and_signs_follow_bdf():
    build = build_thevenin(ECM_PS, initial_soc=1.0)
    result = run_experiment(build, ["Discharge at 1C for 10 minutes"], period_s=30.0)
    voltage = result["voltage_volt"]
    assert len(voltage) > 2
    assert voltage[-1] < voltage[0]  # discharging: voltage falls
    # BDF sign convention: discharge current is negative
    assert all(i <= 0 for i in result["current_ampere"][1:])
    soc = result["state_of_charge"]
    assert soc[-1] < soc[0] < 1.001
