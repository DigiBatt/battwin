# ECM models and simulation

Equivalent-circuit models are the workhorse of applied battery twinning, so battwin gives them first-class support in two strictly separated halves:

- **`battwin.ecm`** (core install) validates that a model binding's payload is a well-formed **ECM Parameter Set (ECM-PS)** document. Validation only; the core package never evaluates a model.
- **`battwin.sim`** (the `battwin[sim]` extra) turns that payload into a PyBaMM Thevenin model and runs experiments against it.

The spec fence is unchanged by the second half: the *format* never specifies execution. Simulation is a convenience of the reference SDK, and everything it computes flows back into the envelope as ordinary spec objects (data links, state snapshots) via `next_version()`.

## ECM Parameter Sets

An ECM-PS document carries equivalent-circuit-model parameters (topology, sign conventions, cell limits, and a lookup or functional parameter table) in an open, semantically typed form: the concepts live in the EMMO domain-equivalent-circuit-model ontology, the values live in the document. A twin attaches one through a model binding whose `inline` payload, or the document behind `source`, is an ECM-PS.

battwin packages the draft ECM-PS JSON Schema (`battwin/schemas/ecm-params.schema.json`) with a small API:

```python
from battwin.ecm import ecm_ps_problems, validate_ecm_ps_file, load_ecm_schema

problems = validate_ecm_ps_file("cell.ecm.json")   # list[str], empty = valid
problems = ecm_ps_problems(doc)                    # same, for a parsed dict
schema = load_ecm_schema()                         # the packaged schema itself
```

!!! note "Provisional schema `$id`"
    The format is co-developed with the EMMO domain-equivalent-circuit-model work, and the schema `$id` under that namespace is provisional until the corresponding w3id redirects are registered.

The ECM-PS support was exercised against a real release: the About:Energy parameter set for the Molicel INR21700-P45B ([Zenodo 10.5281/zenodo.19052626](https://doi.org/10.5281/zenodo.19052626), CC-BY-4.0).

## Running an ECM in PyBaMM

```bash
pip install "battwin[sim]"
```

`build_thevenin` builds a `pybamm.equivalent_circuit.Thevenin` model plus parameter values from an ECM-PS document; `run_experiment` runs PyBaMM experiment instructions against the build and returns plain column lists in BDF naming, ready to write as a `.bdf.csv` and attach to the envelope:

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

Details that matter when you use it:

- **Sign convention.** Returned currents follow BDF (positive = charging); PyBaMM's load-positive sign is flipped for you.
- **2-D lookups.** Parameter lookups are interpolated over (temperature, SoC). Per-temperature SoC grids are resampled onto a common axis, so About:Energy-style tables with slightly different SoC points at each temperature work directly. A `current_ampere` lookup axis is not supported yet and raises a clear error.
- **Hysteresis is projected.** PyBaMM's basic Thevenin has a single OCV, so when an ECM-PS carries charge and discharge branches, their mean is used and the branches are kept only in the document. This and any similar simplification is surfaced explicitly in `TheveninBuild.warnings`.
- **Tables from disk or inline.** `parameters.table` may be an inline row list or the name of a CSV resolved against `base_dir`; `load_table` handles both.

The pipeline was verified end to end against the About:Energy Molicel INR21700-P45B release: a 1C discharge with the twin's version chain running specification → model → simulated state.

## Closing the loop into the envelope

A typical session ends by writing the results back as spec objects:

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

## A note on PyBaMM telemetry

PyBaMM includes opt-out usage telemetry (via `posthog`). If you do not want a local simulation run to report usage, disable it before importing PyBaMM, for example with the `PYBAMM_DISABLE_TELEMETRY=true` environment variable; see the [PyBaMM documentation](https://docs.pybamm.org/) for the current mechanism.
