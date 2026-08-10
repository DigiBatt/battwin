"""Run a twin's ECM model binding in PyBaMM (the ``battwin[sim]`` extra).

This is the execution half of the ECM story: :mod:`battwin.ecm` checks that a
binding's payload is a well-formed ECM Parameter Set; this module turns that
payload into a ``pybamm.equivalent_circuit.Thevenin`` model and runs an
experiment against it. The mapping (PyBaMM-exact parameter names, °C
temperature axis, optional current axis, lossy hysteresis projection, current
sign flip) follows the ECM-PS ⇄ PyBaMM design record.

The spec fence is unchanged: the *format* never specifies execution. This
module is an optional convenience of the reference SDK -- ``pip install
"battwin[sim]"`` -- and everything it computes flows back into the envelope
as ordinary spec objects (data links, state snapshots) via
:meth:`TwinEnvelope.next_version`.

Two deliberate simplifications in this first version, both surfaced in
:attr:`TheveninBuild.warnings`:

* ``Open-circuit voltage [V]`` is the mean of the charge/discharge branches
  when both are present -- PyBaMM's basic Thevenin has a single OCV, so the
  hysteresis branches and decay rate are dropped (kept in the ECM-PS for
  round-trip).
* Lookups are 2-D over (temperature, SoC); a ``current_ampere`` axis, if the
  document declares one, is not yet supported.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["TheveninBuild", "build_thevenin", "load_table", "run_experiment"]

logger = logging.getLogger(__name__)

#: Simulation-environment defaults (thermal jig, initial state) used when the
#: ECM-PS carries no ``thermal``/``initial_conditions`` blocks. These describe
#: the virtual test bench, not the cell; values follow PyBaMM's ECM example set.
_BENCH_DEFAULTS: dict[str, float] = {
    "Cell thermal mass [J/K]": 1000.0,
    "Cell-jig heat transfer coefficient [W/K]": 10.0,
    "Jig thermal mass [J/K]": 500.0,
    "Jig-air heat transfer coefficient [W/K]": 10.0,
    "RCR lookup limit [A]": 100.0,
    "Current function [A]": 0.0,
}


def _require_pybamm() -> Any:
    try:
        import pybamm
    except ImportError as exc:
        raise ImportError(
            "simulation requires the optional dependency pybamm; install it with: "
            'pip install "battwin[sim]"'
        ) from exc
    return pybamm


@dataclass
class TheveninBuild:
    """A ready-to-run PyBaMM Thevenin model built from an ECM-PS document."""

    model: Any
    parameter_values: Any
    options: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def load_table(ecm_ps: dict[str, Any], *, base_dir: str | Path | None = None) -> list[dict]:
    """Load the ECM-PS lookup table as rows of floats keyed by column name.

    ``parameters.table`` names a CSV relative to ``base_dir`` (default: the
    current directory). An inline table (a list of row objects) is returned
    as-is with values coerced to float.
    """
    table = ecm_ps.get("parameters", {}).get("table")
    if isinstance(table, list):
        return [{k: float(v) for k, v in row.items()} for row in table]
    if not isinstance(table, str):
        raise ValueError("ECM-PS parameters.table must be a filename or inline row list")
    path = Path(base_dir or ".") / table
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def build_thevenin(
    ecm_ps: dict[str, Any],
    *,
    table: list[dict] | None = None,
    base_dir: str | Path | None = None,
    initial_soc: float = 1.0,
    ambient_celsius: float = 25.0,
) -> TheveninBuild:
    """Build a PyBaMM Thevenin model + parameter values from an ECM-PS document.

    ``table`` overrides loading ``parameters.table`` from disk. The lookup is
    resampled onto a common SoC grid per temperature (About:Energy-style
    tables have slightly different SoC points at each temperature), and every
    R/C interpolant ignores the current argument (2-D lookup).
    """
    pybamm = _require_pybamm()
    import numpy as np  # a pybamm dependency: guaranteed present once pybamm is

    warnings: list[str] = []

    axes = {a.get("name") for a in ecm_ps.get("parameters", {}).get("independent_variables", [])}
    if "current_ampere" in axes:
        raise ValueError("a current_ampere lookup axis is not supported yet (2-D only)")

    rows = table if table is not None else load_table(ecm_ps, base_dir=base_dir)
    temps = sorted({r["temperature_degc"] for r in rows})
    by_temp = {
        t: sorted((r["state_of_charge"], r) for r in rows if r["temperature_degc"] == t)
        for t in temps
    }

    # Common SoC axis: the union of every temperature's grid, resampled per
    # temperature with 1-D linear interpolation so the (T, SoC) matrix is
    # regular -- pybamm.Interpolant needs a product grid.
    soc_axis = np.array(sorted({r["state_of_charge"] for r in rows}))
    temp_axis = np.array(temps)

    def matrix(column: str) -> np.ndarray:
        out = np.empty((len(temps), len(soc_axis)))
        for i, t in enumerate(temps):
            socs = np.array([s for s, _ in by_temp[t]])
            vals = np.array([r[column] for _, r in by_temp[t]])
            out[i] = np.interp(soc_axis, socs, vals)
        return out

    columns = {c["name"] for c in ecm_ps["parameters"]["columns"]}

    # OCV: single f(SoC) at the temperature nearest ambient; mean of the
    # hysteresis branches when both exist (lossy -- PyBaMM-basic has one OCV).
    t_ref = int(np.argmin(np.abs(temp_axis - ambient_celsius)))
    if {"ocv_charge_volt", "ocv_discharge_volt"} <= columns:
        ocv_curve = 0.5 * (matrix("ocv_charge_volt")[t_ref] + matrix("ocv_discharge_volt")[t_ref])
        warnings.append(
            "OCV hysteresis dropped: PyBaMM basic Thevenin uses a single "
            "Open-circuit voltage [V]; the charge/discharge branches were averaged "
            f"at {temps[t_ref]:g} degC and the decay rate is unused."
        )
    elif "ocv_volt" in columns:
        ocv_curve = matrix("ocv_volt")[t_ref]
    else:
        raise ValueError("ECM-PS table carries no OCV column")

    def interp2d(column: str, label: str):
        y = matrix(column)

        def f(T_cell, current, soc):  # PyBaMM calls f(T [degC], I [A], SoC); I ignored (2-D)
            return pybamm.Interpolant(
                [temp_axis, soc_axis], y, [T_cell, soc], name=label, extrapolate=True
            )

        return f

    n_rc = int(ecm_ps.get("topology", {}).get("rc_branches", 1))
    cell = ecm_ps["cell"]
    capacity = float(cell["nominal_capacity_ampere_hour"])
    values: dict[str, Any] = {
        "Nominal cell capacity [A.h]": capacity,
        "Cell capacity [A.h]": capacity,
        "Upper voltage cut-off [V]": float(cell["upper_cutoff_voltage_volt"]),
        "Lower voltage cut-off [V]": float(cell["lower_cutoff_voltage_volt"]),
        "Open-circuit voltage [V]": (
            lambda soc: pybamm.Interpolant(soc_axis, ocv_curve, soc, name="OCV", extrapolate=True)
        ),
        "R0 [Ohm]": interp2d("series_resistance_ohm", "R0"),
        # PyBaMM's Maximum/Minimum SoC events fire AT the bounds, so an
        # initial SoC of exactly 1.0 (or 0.0) terminates at t=0; clamp to the
        # open interval.
        "Initial SoC": min(max(float(initial_soc), 1e-6), 1.0 - 1e-6),
        "Initial temperature [K]": 273.15 + float(ambient_celsius),
        "Ambient temperature [K]": 273.15 + float(ambient_celsius),
        **_BENCH_DEFAULTS,
    }
    for i in range(1, n_rc + 1):
        values[f"R{i} [Ohm]"] = interp2d(f"polarization_resistance_{i}_ohm", f"R{i}")
        values[f"C{i} [F]"] = interp2d(f"polarization_capacitance_{i}_farad", f"C{i}")
        values[f"Element-{i} initial overpotential [V]"] = 0.0

    if "entropic_coefficient_volt_per_kelvin" in columns:
        dudt = matrix("entropic_coefficient_volt_per_kelvin")
        # PyBaMM's entropic change is f(OCV [V], T [degC]): re-axis the (T, SoC)
        # matrix over (OCV, T) using the reference OCV curve. The curve can
        # carry duplicate values (flat regions), and the grid interpolator
        # needs a strictly monotonic axis, so keep one sample per unique OCV.
        ocv_axis, unique_idx = np.unique(ocv_curve, return_index=True)
        dudt_by_ocv = dudt[:, unique_idx].T  # shape (n_unique_ocv, n_T)

        def entropic(ocv, T_cell):
            return pybamm.Interpolant(
                [ocv_axis, temp_axis],
                dudt_by_ocv,
                [ocv, T_cell],
                name="dUdT",
                extrapolate=True,
            )

        values["Entropic change [V/K]"] = entropic
    else:
        values["Entropic change [V/K]"] = 0.0

    options = {"number of rc elements": n_rc}
    model = pybamm.equivalent_circuit.Thevenin(options=options)
    parameter_values = pybamm.ParameterValues(values)
    for warning in warnings:
        logger.warning(warning)
    return TheveninBuild(
        model=model, parameter_values=parameter_values, options=options, warnings=warnings
    )


def run_experiment(
    build: TheveninBuild,
    instructions: list[str],
    *,
    period_s: float = 10.0,
) -> dict[str, list[float]]:
    """Run a PyBaMM experiment against a built Thevenin model.

    ``instructions`` are PyBaMM experiment strings (e.g. ``"Discharge at 1C
    until 2.5 V"``). Returns plain column lists in BDF naming (positive
    current = charging, per the BDF sign convention -- PyBaMM's load-positive
    sign is flipped here) so callers can write a ``.bdf.csv`` and attach it
    to the envelope as a data link.
    """
    pybamm = _require_pybamm()
    experiment = pybamm.Experiment(instructions, period=f"{period_s} seconds")
    simulation = pybamm.Simulation(
        build.model, parameter_values=build.parameter_values, experiment=experiment
    )
    solution = simulation.solve()
    return {
        "test_time_second": [float(v) for v in solution["Time [s]"].entries],
        "voltage_volt": [float(v) for v in solution["Voltage [V]"].entries],
        # BDF sign: positive charges the cell; PyBaMM current is load-positive.
        "current_ampere": [-float(v) for v in solution["Current [A]"].entries],
        "state_of_charge": [float(v) for v in solution["SoC"].entries],
        "surface_temperature_celsius": [
            float(v) for v in solution["Cell temperature [degC]"].entries
        ],
    }
