"""Fit a twin's ECM parameters against measured data (the ``battwin[fit]`` extra).

This closes the loop the tutorials walk one way: a twin links measured data
(:class:`~battwin.envelope.DataLink`), and this module uses `PyBOP
<https://github.com/pybop-team/PyBOP>`_ to identify circuit parameters from
that data, returning a **new** ECM-PS document with the fitted constants and
the fit's provenance recorded in the document's ``User-defined`` section. The
caller attaches the result to the twin as a new model binding via
:meth:`TwinEnvelope.next_version` -- outputs land back in the envelope as
ordinary spec objects, like everything else in the reference SDK.

Scope, stated plainly: parameters are fitted as **constants** (a fitted value
replaces whatever the base document carried for that name, including a 2-D
table -- surfaced in :attr:`FitResult.warnings`). Identifying full
SoC/temperature lookup surfaces from one dataset is ill-posed and out of
scope. OCV curves are not fittable here either; they come from
characterization, not regression against a drive trace.
"""

from __future__ import annotations

import csv
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .sim import _Value, build_thevenin

__all__ = ["FitResult", "fit_thevenin", "read_bdf"]

#: Circuit parameter names eligible for fitting: R0 and the RC-branch pairs.
_FITTABLE_PREFIXES = ("R", "C")


def _require_pybop() -> Any:
    try:
        import pybop
    except ImportError as exc:
        raise ImportError(
            "parameter fitting requires the optional dependency pybop; install it "
            'with: pip install "battwin[fit]"'
        ) from exc
    return pybop


def read_bdf(path: str | Path) -> dict[str, list[float]]:
    """Read a BDF-convention CSV into columns of floats keyed by column name."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return {name: [float(r[name]) for r in rows] for name in rows[0]}


@dataclass
class FitResult:
    """The outcome of :func:`fit_thevenin`."""

    ecm_ps: dict[str, Any]
    """A new ECM-PS document: fitted constants in place, provenance in User-defined."""

    fitted: dict[str, float]
    """Fitted parameter values by Circuit name."""

    rmse_volt: float
    """Root-mean-square voltage error of the fitted model over the dataset."""

    initial_rmse_volt: float
    """The same cost at the initial values, for before/after comparison."""

    n_iterations: int
    warnings: list[str] = field(default_factory=list)


def fit_thevenin(
    ecm_ps: dict[str, Any],
    data: Mapping[str, Sequence[float]],
    *,
    fit: Iterable[str] = ("R0 [Ohm]",),
    initial: Mapping[str, float] | None = None,
    bounds: Mapping[str, tuple[float, float]] | None = None,
    initial_soc: float = 1.0,
    ambient_celsius: float = 25.0,
    max_iterations: int = 1000,
    source_data: str | None = None,
) -> FitResult:
    """Fit Circuit parameters of an ECM-PS document to measured data.

    ``data`` is a mapping of BDF-named columns (``test_time_second``,
    ``current_ampere`` with the BDF positive-=-charging sign, and
    ``voltage_volt``), e.g. the columns of a dataset the twin links --
    :func:`read_bdf` reads one from disk. ``fit`` names the Circuit
    parameters to identify (``"R0 [Ohm]"``, ``"R1 [Ohm]"``, ``"C1 [F]"``,
    ...); each is fitted as a constant, starting from ``initial`` (default:
    the base document's value at ambient temperature and mid-SoC) within
    ``bounds`` (default: a factor of 10 either side of the start).

    Returns a :class:`FitResult` whose ``ecm_ps`` is a new, schema-valid
    document; ``source_data``, when given, is recorded in the fit provenance
    so the fitted model names the dataset it was calibrated against.
    """
    pybop = _require_pybop()
    import numpy as np  # a pybamm dependency: guaranteed present once pybop is

    from .ecm import ecm_ps_problems

    fit_names = list(fit)
    if not fit_names:
        raise ValueError("fit must name at least one Circuit parameter")
    circuit = ecm_ps["Parameterisation"]["Circuit"]
    for name in fit_names:
        if not name.startswith(_FITTABLE_PREFIXES) or "[" not in name:
            raise ValueError(
                f"cannot fit {name!r}: only R/C circuit parameters are fittable "
                "(OCV curves come from characterization, not regression)"
            )
        if name not in circuit:
            raise ValueError(f"cannot fit {name!r}: not present in the Circuit section")

    build = build_thevenin(ecm_ps, initial_soc=initial_soc, ambient_celsius=ambient_celsius)
    warnings = list(build.warnings)

    t = np.asarray(data["test_time_second"], dtype=float)
    # BDF sign is positive = charging; PyBaMM current is load-positive.
    i_load = -np.asarray(data["current_ampere"], dtype=float)
    v = np.asarray(data["voltage_volt"], dtype=float)

    parameters: dict[str, Any] = {}
    starts: dict[str, float] = {}
    for name in fit_names:
        base_value = _Value(name, circuit[name])
        if initial and name in initial:
            x0 = float(initial[name])
        elif base_value.kind == "const":
            x0 = base_value.const
        else:
            soc_axis, vals, _ = base_value.curve_at(ambient_celsius, np)
            x0 = float(np.interp(0.5, soc_axis, vals))
            warnings.append(
                f"{name}: table value replaced by a fitted constant "
                f"(start {x0:.6g} from mid-SoC at {ambient_celsius:g} degC)"
            )
        starts[name] = x0
        lo, hi = (bounds or {}).get(name, (x0 / 10.0, x0 * 10.0))
        parameters[name] = pybop.Parameter(initial_value=x0, bounds=(lo, hi))

    parameter_values = build.parameter_values
    parameter_values.update(parameters)

    dataset = pybop.Dataset({"Time [s]": t, "Current [A]": i_load, "Voltage [V]": v})
    simulator = pybop.pybamm.Simulator(
        build.model,
        parameter_values=parameter_values,
        protocol=dataset,
        output_variables=["Voltage [V]"],
    )
    cost = pybop.RootMeanSquaredError(dataset, target="Voltage [V]")
    problem = pybop.Problem(simulator, cost)
    optimiser = pybop.SciPyMinimize(
        problem, options=pybop.SciPyMinimizeOptions(maxiter=max_iterations)
    )
    result = optimiser.run()

    fitted = {name: float(value) for name, value in result.best_inputs.items()}

    new_doc = deepcopy(ecm_ps)
    new_circuit = new_doc["Parameterisation"]["Circuit"]
    for name, value in fitted.items():
        new_circuit[name] = value
    provenance: dict[str, Any] = {
        "tool": "battwin.fit (PyBOP SciPyMinimize, RootMeanSquaredError on Voltage [V])",
        "fitted": fitted,
        "initial": starts,
        "rmse_volt": float(result.best_cost),
        "initial_rmse_volt": float(result.initial_cost),
        "n_iterations": int(result.n_iterations),
        "ambient_celsius": float(ambient_celsius),
        "initial_soc": float(initial_soc),
    }
    if source_data is not None:
        provenance["source_data"] = source_data
    user_defined = new_doc["Parameterisation"].setdefault("User-defined", {})
    user_defined["pybop"] = provenance

    problems = ecm_ps_problems(new_doc)
    if problems:  # pragma: no cover - guards an internal invariant
        raise RuntimeError(f"fitted document failed validation: {problems}")

    return FitResult(
        ecm_ps=new_doc,
        fitted=fitted,
        rmse_volt=float(result.best_cost),
        initial_rmse_volt=float(result.initial_cost),
        n_iterations=int(result.n_iterations),
        warnings=warnings,
    )
