# Fit ECM parameters

Identify circuit parameters of an ECM-PS document from measured data with PyBOP, getting back a new, schema-valid document with the fitted constants and full fit provenance. Requires the `fit` extra:

```bash
pip install "battwin[fit]"
```

## Fit against a twin's linked data

```python
from battwin import load
from battwin.fit import fit_thevenin, read_bdf

env = load("cell.twin.json")
link = next(d for d in env.data if d.role == "characterization")

result = fit_thevenin(
    env.models[0].inline,          # the ECM-PS document to calibrate
    read_bdf(link.uri),            # BDF columns: test_time_second, current_ampere, voltage_volt
    fit=["R0 [Ohm]"],              # which Circuit parameters to identify
    initial_soc=1.0,
    ambient_celsius=25.0,
    source_data=link.uri,          # recorded in the fit provenance
)

result.fitted              # {"R0 [Ohm]": 0.01865}
result.rmse_volt           # residual RMS voltage error (V)
result.initial_rmse_volt   # the same cost before fitting
result.ecm_ps              # new document: fitted constants + User-defined provenance
```

The data columns follow BDF naming and sign (positive = charging); `fit_thevenin` flips to PyBaMM's load-positive convention internally, and drives the simulation with the *measured* current profile, so any protocol works as fitting data, not just constant current.

## Defaults, and how to override them

Initial values
: taken from the base document (a table's value at ambient temperature and mid-SoC, with a warning that the fitted constant replaces the table); override per parameter with `initial={"R0 [Ohm]": 0.01}`.

Bounds
: a factor of 10 either side of the initial value; override with `bounds={"R0 [Ohm]": (0.001, 0.05)}`. A fitted value *at* a bound is a red flag — see below.

Optimiser
: PyBOP's `SciPyMinimize` minimising RMS voltage error, capped by `max_iterations`.

## Attach the result to the twin

The fitted document is an ordinary ECM-PS; give it its own binding beside the original (sections replace wholesale, so carry the existing bindings forward), with a `validity` window matching the conditions it was fitted under:

```python
from battwin import ModelBinding, ValidityWindow, save

v2 = env.next_version(
    models=list(env.models) + [
        ModelBinding(kind="custom", name="calibrated (bench 1C, 25 degC)",
                     inline=result.ecm_ps,
                     validity=ValidityWindow(temperature_celsius=(20.0, 30.0)))
    ]
)
save(v2, "cell.v2.twin.json")
```

## What is fittable, honestly

- Only R/C circuit parameters (`"R0 [Ohm]"`, `"R1 [Ohm]"`, `"C1 [F]"`, ...) can be fitted, each as a **constant**. OCV curves are not fittable here; they come from characterization.
- **Name only what your data can identify.** A smooth constant-current discharge determines the *effective total* resistance well, but cannot separate R0 from the RC branches — fitting all of them on such data drives parameters to their bounds while the cost barely improves. Dynamic data (pulses, GITT, drive cycles) is what separates the time constants.
- Fit provenance lands in the result document's `User-defined` section under `"pybop"`: optimiser, initial and fitted values, residuals, iteration count, conditions, and the `source_data` URI, so a fitted model always names its evidence.

## Related

- The tutorial [Fit the model to your cell](../tutorials/fit-model.md) runs this end to end on real data, including the identifiability trap.
- [ECM-PS format](../reference/ecm-ps.md) for the document the fit consumes and produces.
