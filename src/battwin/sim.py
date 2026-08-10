"""Run a twin's ECM model binding in PyBaMM (the ``battwin[sim]`` extra).

This is the execution half of the ECM story: :mod:`battwin.ecm` checks that a
binding's payload is a well-formed ECM Parameter Set; this module turns that
payload into a ``pybamm.equivalent_circuit.Thevenin`` model and runs an
experiment against it. ECM-PS 0.2 is styled after BPX (Header/Parameterisation
sections, bracketed-unit parameter names, scalar-or-table values, Kelvin), and
the mapping here follows the parameter names' own ``-> PyBaMM`` annotations in
the packaged schema.

The spec fence is unchanged: the *format* never specifies execution. This
module is an optional convenience of the reference SDK -- ``pip install
"battwin[sim]"`` -- and everything it computes flows back into the envelope
as ordinary spec objects (data links, state snapshots) via
:meth:`TwinEnvelope.next_version`.

Deliberate simplifications, surfaced in :attr:`TheveninBuild.warnings` or as
errors:

* ``Open-circuit voltage [V]`` is the mean of the charge/discharge branches
  when both are present -- PyBaMM's basic Thevenin has a single OCV, so the
  hysteresis branches and decay rate are dropped (kept in the ECM-PS for
  round-trip).
* Expression-string values are not part of ECM-PS and are rejected with a
  clear error; only constants and 1-D/2-D interpolated tables are evaluated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

__all__ = ["TheveninBuild", "build_thevenin", "run_experiment"]

logger = logging.getLogger(__name__)

#: Simulation-environment defaults (thermal jig, initial state) used when the
#: ECM-PS carries no thermal keys. These describe the virtual test bench, not
#: the cell; values follow PyBaMM's ECM example set.
_BENCH_DEFAULTS: dict[str, float] = {
    "Cell thermal mass [J/K]": 1000.0,
    "Cell-jig heat transfer coefficient [W/K]": 10.0,
    "Jig thermal mass [J/K]": 500.0,
    "Jig-air heat transfer coefficient [W/K]": 10.0,
    "RCR lookup limit [A]": 100.0,
    "Current function [A]": 0.0,
}

#: ECM-PS Cell thermal keys (BPX dot-units) -> PyBaMM parameter names.
_THERMAL_KEYS: dict[str, str] = {
    "Cell thermal mass [J.K-1]": "Cell thermal mass [J/K]",
    "Cell-jig heat transfer coefficient [W.K-1]": "Cell-jig heat transfer coefficient [W/K]",
    "Jig thermal mass [J.K-1]": "Jig thermal mass [J/K]",
    "Jig-air heat transfer coefficient [W.K-1]": "Jig-air heat transfer coefficient [W/K]",
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


class _Value:
    """A Circuit parameter value: constant, 1-D table over SoC, or 2-D over (SoC, T[K])."""

    def __init__(self, name: str, raw: Any) -> None:
        self.name = name
        if isinstance(raw, (int, float)):
            self.kind = "const"
            self.const = float(raw)
        elif isinstance(raw, dict) and "z" in raw:
            self.kind = "2d"
            self.soc = [float(v) for v in raw["x"]]
            self.temp_k = [float(v) for v in raw["y"]]
            self.z = [[float(v) for v in row] for row in raw["z"]]
        elif isinstance(raw, dict) and {"x", "y"} <= set(raw):
            self.kind = "1d"
            self.soc = [float(v) for v in raw["x"]]
            self.vals = [float(v) for v in raw["y"]]
        else:
            raise ValueError(
                f"unsupported value for {name!r}: expected a number or an interpolated "
                "table; ECM-PS has no expression strings"
            )

    def curve_at(self, ambient_celsius: float, np: Any) -> tuple[Any, Any, float]:
        """A 1-D (soc_axis, values) view, picking the nearest temperature row for 2-D."""
        if self.kind == "const":
            axis = np.array([0.0, 1.0])
            return axis, np.full(2, self.const), ambient_celsius
        if self.kind == "1d":
            return np.array(self.soc), np.array(self.vals), ambient_celsius
        temps_c = np.array(self.temp_k) - 273.15
        i = int(np.argmin(np.abs(temps_c - ambient_celsius)))
        return np.array(self.soc), np.array(self.z[i]), float(temps_c[i])


def build_thevenin(
    ecm_ps: dict[str, Any],
    *,
    initial_soc: float = 1.0,
    ambient_celsius: float = 25.0,
) -> TheveninBuild:
    """Build a PyBaMM Thevenin model + parameter values from an ECM-PS 0.2 document.

    Constants pass through; 1-D tables become SoC interpolants; 2-D tables
    become (temperature, SoC) interpolants (the document's Kelvin axis is
    converted to the Celsius axis PyBaMM's ECM callbacks use).
    """
    pybamm = _require_pybamm()
    import numpy as np  # a pybamm dependency: guaranteed present once pybamm is

    warnings: list[str] = []

    param = ecm_ps["Parameterisation"]
    cell = param["Cell"]
    circuit = param["Circuit"]
    n_rc = int(cell["Number of RC elements"])

    def value(name: str) -> _Value:
        if name not in circuit:
            raise ValueError(f"Circuit is missing {name!r} (Number of RC elements = {n_rc})")
        return _Value(name, circuit[name])

    def rc_callable(v: _Value, label: str):
        """PyBaMM R/C callback f(T [degC], I [A], SoC); the current argument is unused."""
        if v.kind == "const":
            return v.const
        if v.kind == "1d":
            soc_axis, vals = np.array(v.soc), np.array(v.vals)

            def f1(T_cell, current, soc):
                return pybamm.Interpolant(soc_axis, vals, soc, name=label, extrapolate=True)

            return f1
        soc_axis = np.array(v.soc)
        temp_axis = np.array(v.temp_k) - 273.15
        z = np.array(v.z)

        def f2(T_cell, current, soc):
            return pybamm.Interpolant(
                [temp_axis, soc_axis], z, [T_cell, soc], name=label, extrapolate=True
            )

        return f2

    # OCV: single f(SoC); mean of the hysteresis branches when both exist
    # (lossy -- PyBaMM-basic has one OCV). 2-D branches are read at the
    # temperature nearest ambient.
    if "Open-circuit voltage [V]" in circuit:
        ocv = value("Open-circuit voltage [V]")
        ocv_soc_axis, ocv_curve, _ = ocv.curve_at(ambient_celsius, np)
    else:
        charge = value("Open-circuit voltage on charge [V]")
        discharge = value("Open-circuit voltage on discharge [V]")
        ocv_soc_axis, charge_curve, t_used = charge.curve_at(ambient_celsius, np)
        _, discharge_curve, _ = discharge.curve_at(ambient_celsius, np)
        if len(charge_curve) != len(discharge_curve):
            raise ValueError("OCV charge/discharge branches must share a SoC grid")
        ocv_curve = 0.5 * (charge_curve + discharge_curve)
        warnings.append(
            "OCV hysteresis dropped: PyBaMM basic Thevenin uses a single "
            "Open-circuit voltage [V]; the charge/discharge branches were averaged "
            f"at {t_used:g} degC and the decay rate is unused."
        )

    capacity = float(cell["Nominal cell capacity [A.h]"])
    values: dict[str, Any] = {
        "Nominal cell capacity [A.h]": capacity,
        "Cell capacity [A.h]": capacity,
        "Upper voltage cut-off [V]": float(cell["Upper voltage cut-off [V]"]),
        "Lower voltage cut-off [V]": float(cell["Lower voltage cut-off [V]"]),
        "Open-circuit voltage [V]": (
            lambda soc: pybamm.Interpolant(
                ocv_soc_axis, ocv_curve, soc, name="OCV", extrapolate=True
            )
        ),
        "R0 [Ohm]": rc_callable(value("R0 [Ohm]"), "R0"),
        # PyBaMM's Maximum/Minimum SoC events fire AT the bounds, so an
        # initial SoC of exactly 1.0 (or 0.0) terminates at t=0; clamp to the
        # open interval.
        "Initial SoC": min(max(float(initial_soc), 1e-6), 1.0 - 1e-6),
        "Initial temperature [K]": 273.15 + float(ambient_celsius),
        "Ambient temperature [K]": 273.15 + float(ambient_celsius),
        **_BENCH_DEFAULTS,
    }
    for ecm_key, pybamm_key in _THERMAL_KEYS.items():
        if ecm_key in cell:
            values[pybamm_key] = float(cell[ecm_key])
    for i in range(1, n_rc + 1):
        values[f"R{i} [Ohm]"] = rc_callable(value(f"R{i} [Ohm]"), f"R{i}")
        values[f"C{i} [F]"] = rc_callable(value(f"C{i} [F]"), f"C{i}")
        values[f"Element-{i} initial overpotential [V]"] = 0.0

    if "Entropic change [V.K-1]" in circuit:
        dudt = _Value("Entropic change [V.K-1]", circuit["Entropic change [V.K-1]"])
        if dudt.kind == "const":
            values["Entropic change [V/K]"] = dudt.const
        else:
            # PyBaMM's entropic change is f(OCV [V], T [degC]): re-axis over
            # (OCV, T) using the reference OCV curve. The curve can carry
            # duplicate values (flat regions), and the grid interpolator needs
            # a strictly monotonic axis, so keep one sample per unique OCV.
            ocv_axis, unique_idx = np.unique(ocv_curve, return_index=True)
            if dudt.kind == "1d":
                vals_on_soc = np.interp(ocv_soc_axis, np.array(dudt.soc), np.array(dudt.vals))
                on_ocv_grid = vals_on_soc[unique_idx]

                def entropic_1d(ocv, T_cell):
                    return pybamm.Interpolant(
                        ocv_axis, on_ocv_grid, ocv, name="dUdT", extrapolate=True
                    )

                values["Entropic change [V/K]"] = entropic_1d
            else:
                z = np.array([np.interp(ocv_soc_axis, np.array(dudt.soc), row) for row in dudt.z])
                dudt_by_ocv = z[:, unique_idx].T  # shape (n_unique_ocv, n_T)
                temp_axis = np.array(dudt.temp_k) - 273.15

                def entropic_2d(ocv, T_cell):
                    return pybamm.Interpolant(
                        [ocv_axis, temp_axis],
                        dudt_by_ocv,
                        [ocv, T_cell],
                        name="dUdT",
                        extrapolate=True,
                    )

                values["Entropic change [V/K]"] = entropic_2d
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
