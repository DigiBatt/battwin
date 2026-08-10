# Simulate a twin's ECM

In this tutorial you will attach an equivalent-circuit model to a twin, run a 1C discharge with PyBaMM, and commit the simulated state back into the twin's version chain. It continues from [Your first twin](first-twin.md); you should be comfortable with `next_version()` before starting.

You need the `sim` extra and an ECM Parameter Set. We use the openly licensed About:Energy parameter release for the Molicel INR21700-P45B cell, the same dataset the feature was verified against.

## 1. Install the sim extra

```bash
pip install "battwin[sim]"
```

This pulls in PyBaMM. PyBaMM includes opt-out usage telemetry; if you do not want simulation runs reported, set `PYBAMM_DISABLE_TELEMETRY=true` in your environment before importing it (see the [PyBaMM documentation](https://docs.pybamm.org/) for the current mechanism).

## 2. Get an ECM Parameter Set

Download the About:Energy Molicel INR21700-P45B release from [Zenodo (10.5281/zenodo.19052626)](https://doi.org/10.5281/zenodo.19052626) (CC-BY-4.0) and place the ECM-PS JSON document and its lookup-table CSV in your working directory. Then confirm the document is well formed:

```python
from battwin.ecm import validate_ecm_ps_file

assert validate_ecm_ps_file("p45b.ecm.json") == []
```

An ECM-PS carries the model's topology, sign conventions, cell limits, and a parameter lookup table; the concepts are typed against the EMMO domain-equivalent-circuit-model ontology.

## 3. Attach the model to a twin

```python
import json
from battwin import ModelBinding, ValidityWindow, load, save

v2 = load("cell.v2.twin.json")
v3 = v2.next_version(
    models=[
        ModelBinding(
            kind="custom",
            name="p45b-ecm",
            source="p45b.ecm.json",
            validity=ValidityWindow(
                temperature_celsius=(0.0, 45.0),
                state_of_charge=(0.05, 1.0),
            ),
        )
    ]
)
save(v3, "cell.v3.twin.json")
```

The envelope now *names* the model and its trusted operating window. It does not embed PyBaMM, a solver, or any execution instructions; that separation is the core of the format.

## 4. Build and run the model

```python
import json
from battwin.sim import build_thevenin, run_experiment

ecm_ps = json.load(open("p45b.ecm.json"))
build = build_thevenin(ecm_ps, initial_soc=1.0, ambient_celsius=25.0)
for w in build.warnings:
    print("warning:", w)

columns = run_experiment(build, ["Discharge at 1C until 2.5 V"], period_s=10.0)
```

Watch the warnings: if the parameter set carries OCV hysteresis branches, you will be told that their mean is used, because PyBaMM's basic Thevenin model has a single OCV.

`columns` is a plain dict of lists in BDF naming (`test_time_second`, `voltage_volt`, `current_ampere`, `state_of_charge`, `surface_temperature_celsius`), with the current sign already flipped to the BDF convention (positive = charging).

## 5. Commit the results into the chain

Write the columns as a BDF CSV, then issue the next version with a data link and a state snapshot:

```python
import csv
from datetime import datetime, timezone
from battwin import DataLink, StateSnapshot, load, save

with open("sim/discharge_1c.bdf.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(columns.keys())
    writer.writerows(zip(*columns.values()))

v3 = load("cell.v3.twin.json")
v4 = v3.next_version(
    data=list(v3.data) + [DataLink(kind="bdf", uri="sim/discharge_1c.bdf.csv", role="simulation")],
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=columns["state_of_charge"][-1],
        method="ecm_simulation",
        source_data="sim/discharge_1c.bdf.csv",
    ),
)
save(v4, "cell.v4.twin.json")
```

Check the whole story:

```console
$ battwin diff cell.v3.twin.json cell.v4.twin.json
versions: 3 -> 4
changed sections: data, state
version chain: intact (b.previous == hash(a))
```

## 6. Where you are now

Your twin's chain now runs specification → model → simulated state, and every step is an ordinary spec object in an immutable document. Anyone you hand these files to can re-verify the chain and re-run the model with their own tooling.

For the details behind what you just used, see [Run an ECM simulation](../howto/run-ecm.md) (the task-shaped version, including the 2-D lookup and resampling behavior) and the [API reference](../reference/api.md).
