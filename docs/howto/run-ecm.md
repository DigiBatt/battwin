# Run an ECM simulation

Turn a model binding's ECM Parameter Set into a PyBaMM Thevenin model, run experiments, and get BDF-named results ready to attach to the envelope. Requires the `sim` extra:

```bash
pip install "battwin[sim]"
```

## Build and run

```python
import json
from battwin.sim import build_thevenin, run_experiment

ecm_ps = json.load(open("cell.ecm.json"))
build = build_thevenin(ecm_ps, initial_soc=1.0, ambient_celsius=25.0)
for w in build.warnings:
    print("warning:", w)

columns = run_experiment(build, ["Discharge at 1C until 2.5 V"], period_s=10.0)
# columns: test_time_second, voltage_volt, current_ampere,
#          state_of_charge, surface_temperature_celsius
```

`instructions` are ordinary PyBaMM experiment strings, so multi-step protocols (`"Charge at C/2 until 4.2 V"`, `"Hold at 4.2 V until C/50"`, ...) work as-is.

## Behavior that matters

Sign convention
: Returned currents follow BDF (positive = charging); PyBaMM's load-positive sign is flipped for you.

2-D lookups
: Parameter lookups are interpolated over (temperature, SoC). Per-temperature SoC grids are resampled onto a common axis, so About:Energy-style tables with slightly different SoC points at each temperature work directly. A `current_ampere` lookup axis is not supported yet and raises a clear error.

Hysteresis is projected
: PyBaMM's basic Thevenin has a single OCV, so when an ECM-PS carries charge and discharge branches, their mean is used; the branches stay untouched in the document. This and any similar simplification is surfaced in `TheveninBuild.warnings`.

Tables from disk or inline
: `parameters.table` may be an inline row list or the name of a CSV resolved against `base_dir`; `load_table` handles both.

## Write the results back

Simulation output goes back into the envelope as ordinary spec objects, keeping all runtime activity inside the hash-chained document:

```python
from datetime import datetime, timezone
from battwin import DataLink, StateSnapshot, load, save

v1 = load("cell.twin.json")
v2 = v1.next_version(
    data=list(v1.data) + [DataLink(kind="bdf", uri="sim/discharge_1c.bdf.csv", role="simulation")],
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=columns["state_of_charge"][-1],
        method="ecm_simulation",
        source_data="sim/discharge_1c.bdf.csv",
    ),
)
save(v2, "cell.v2.twin.json")
```

```{admonition} PyBaMM telemetry
:class: note

PyBaMM includes opt-out usage telemetry (via `posthog`). To keep a local run from reporting usage, set `PYBAMM_DISABLE_TELEMETRY=true` before importing PyBaMM; see the [PyBaMM documentation](https://docs.pybamm.org/) for the current mechanism.
```

## Related

- The tutorial [Simulate a twin's ECM](../tutorials/simulate-ecm.md) walks the full workflow end to end with a real parameter set.
- [Why simulation lives in an extra](../explanation/design.md) covers the spec fence this feature sits behind.
