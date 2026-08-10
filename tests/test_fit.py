"""Tests for the ``battwin[fit]`` PyBOP parameter-identification adapter.

The suite skips cleanly when pybop is not installed (the same pattern as
``test_sim.py``). The end-to-end test generates synthetic data from a known
R0, perturbs the document, and checks the fit recovers the truth.
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from battwin.ecm import ecm_ps_problems
from battwin.fit import fit_thevenin, read_bdf

pybop_missing = importlib.util.find_spec("pybop") is None
needs_pybop = pytest.mark.skipif(pybop_missing, reason="fit tests need battwin[fit] (pybop)")

ECM_PS = {
    "Header": {
        "ECM-PS version": "0.2",
        "Model": "ECM",
        "Title": "Synthetic 1-RC fitting target",
    },
    "Parameterisation": {
        "Cell": {
            "Nominal cell capacity [A.h]": 4.5,
            "Upper voltage cut-off [V]": 4.3,
            "Lower voltage cut-off [V]": 2.5,
            "Number of RC elements": 1,
        },
        "Circuit": {
            "Open-circuit voltage [V]": {"x": [0.0, 0.5, 1.0], "y": [3.0, 3.6, 4.2]},
            "R0 [Ohm]": 0.008,
            "R1 [Ohm]": 0.003,
            "C1 [F]": 1500.0,
        },
    },
}

_COLUMNS = ["test_time_second", "current_ampere", "voltage_volt"]


def _synthetic_data() -> dict[str, list[float]]:
    from battwin.sim import build_thevenin, run_experiment

    build = build_thevenin(ECM_PS, initial_soc=0.9)
    result = run_experiment(build, ["Discharge at 1C for 10 minutes"], period_s=10.0)
    return {name: result[name] for name in _COLUMNS}


def test_read_bdf_roundtrip(tmp_path):
    target = tmp_path / "t.bdf.csv"
    target.write_text(
        "test_time_second,current_ampere,voltage_volt\n0,-4.5,4.1\n10,-4.5,4.0\n",
        encoding="utf-8",
    )
    columns = read_bdf(target)
    assert columns["voltage_volt"] == [4.1, 4.0]


def test_read_bdf_rejects_header_only_file(tmp_path):
    target = tmp_path / "empty.bdf.csv"
    target.write_text("test_time_second,voltage_volt\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no data rows"):
        read_bdf(target)


def test_fit_without_pybop_raises_actionable_import_error():
    if not pybop_missing:
        pytest.skip("pybop installed; the error path needs it absent")
    with pytest.raises(ImportError, match=r"battwin\[fit\]"):
        fit_thevenin(ECM_PS, {name: [0.0, 1.0] for name in _COLUMNS})


@needs_pybop
def test_non_rc_parameters_are_not_fittable():
    data = {name: [0.0, 1.0] for name in _COLUMNS}
    with pytest.raises(ValueError, match="characterization"):
        fit_thevenin(ECM_PS, data, fit=["Open-circuit voltage [V]"])
    with pytest.raises(ValueError, match="not present"):
        fit_thevenin(ECM_PS, data, fit=["R2 [Ohm]"])
    with pytest.raises(ValueError, match="at least one"):
        fit_thevenin(ECM_PS, data, fit=[])


@needs_pybop
def test_fit_recovers_known_r0_and_records_provenance():
    data = _synthetic_data()
    perturbed = json.loads(json.dumps(ECM_PS))
    perturbed["Parameterisation"]["Circuit"]["R0 [Ohm]"] = 0.02

    result = fit_thevenin(
        perturbed,
        data,
        fit=["R0 [Ohm]"],
        initial_soc=0.9,
        source_data="synthetic.bdf.csv",
    )

    assert result.fitted["R0 [Ohm]"] == pytest.approx(0.008, rel=0.05)
    assert result.rmse_volt < result.initial_rmse_volt
    assert result.rmse_volt < 0.001  # sub-mV on noise-free synthetic data

    doc = result.ecm_ps
    assert ecm_ps_problems(doc) == []
    assert doc["Parameterisation"]["Circuit"]["R0 [Ohm]"] == result.fitted["R0 [Ohm]"]
    provenance = doc["Parameterisation"]["User-defined"]["pybop"]
    assert provenance["source_data"] == "synthetic.bdf.csv"
    assert provenance["initial"]["R0 [Ohm]"] == 0.02
    # the input document is untouched
    assert perturbed["Parameterisation"]["Circuit"]["R0 [Ohm]"] == 0.02
