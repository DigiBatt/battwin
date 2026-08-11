# Fit the model to your cell

This tutorial continues [Link measured data to the twin](link-data.md). Your P45B twin ends that tutorial at version 6 knowing an uncomfortable fact: as battwin simulates it, its model misses the measured discharge by 77 mV RMSE — partly the runtime's own single-OCV projection, partly what any constant-current trace hides. Whatever the cause, the twin links the evidence to fix it. In this tutorial the twin closes the gap itself: PyBOP fits a model parameter against the measurement the twin links, and the calibrated model joins the version chain — ending with the comparison figure below.

As before, every output shown is from a real run (2026-08-10, battwin 0.4.0, PyBOP 26.3).

## 1. Install the fit extra

```bash
pip install "battwin[fit]"
```

This pulls in [PyBOP](https://github.com/pybop-team/PyBOP), the battery optimisation and parameterisation library (it shares the PyBaMM stack the `sim` extra uses).

## 2. Fit R0 from the linked measurement

Save as `fit_model.py`:

```python
import json

from battwin import ModelBinding, ValidityWindow, load, save
from battwin.fit import fit_thevenin, read_bdf

v6 = load("p45b.v6.twin.json")
vendor = v6.models[0]
measured = next(d for d in v6.data if d.role == "characterization")

result = fit_thevenin(
    vendor.inline,                 # the twin's own model binding...
    read_bdf(measured.uri),        # ...fitted to the twin's own linked data
    fit=["R0 [Ohm]"],
    initial_soc=1.0,
    ambient_celsius=25.0,
    source_data=measured.uri,
)
for w in result.warnings:
    print("warning:", w)
print(f"R0 [Ohm]: {result.ecm_ps['Parameterisation']['User-defined']['pybop']['initial']['R0 [Ohm]']:.4g}"
      f" -> {result.fitted['R0 [Ohm]']:.4g}")
print(f"rmse over the measured discharge: {result.initial_rmse_volt*1000:.1f} mV -> {result.rmse_volt*1000:.1f} mV")
```

```console
$ python fit_model.py
warning: R0 [Ohm]: table value replaced by a fitted constant (start 0.00658944 from mid-SoC at 25 degC)
R0 [Ohm]: 0.006589 -> 0.01865
rmse over the measured discharge: 77.6 mV -> 55.6 mV
```

Three things in that output deserve attention:

- **The warning is the format being honest.** The vendor document carries R0 as a 2-D table over SoC and temperature; a fit against one discharge cannot reproduce a surface, so the fitted document carries a *constant* R0 instead, and battwin says so out loud. Everything else (the OCV branches, the RC tables) stays untouched.
- **The fitted value is diagnosable, not noise.** R0 moved from the vendor's 6.6 mΩ to 18.7 mΩ, landing well inside the fit bounds. Decomposed against [Dickinson et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6861858)'s parameters, that value is almost entirely accounted for: ~10.7 mΩ is the DC lumping of the R1/R2 branches into one constant (the vendor's total 25 °C resistance is 17.3 mΩ), and most of the rest (~6.5 mΩ ≈ 29 mV ÷ 4.5 A) compensates battwin's averaged-OCV hysteresis projection, which reads high on a discharge. Little is left over for aging. A fit will happily absorb *your model's* biases along with the cell's physics; knowing which is which takes exactly the kind of source comparison this bullet just did.
- **Why only R0?** A smooth constant-current discharge cannot separate series resistance from the slow RC branches — ask it to fit all five R/C parameters and the optimiser happily slides R0 to a bound while inflating R2, trading one for the other. Full identification wants dynamic data (pulses, GITT — which the About:Energy release also contains). `fit_thevenin` will fit whatever you name; naming only what your data can identify is your job. See [Fit ECM parameters](../howto/fit-parameters.md).

## 3. Commit the calibrated model as version 7

The twin should carry *both* models — the generic vendor set and the cell-specific calibration — under distinct names. Append to `fit_model.py`:

```python
v7 = v6.next_version(
    models=[
        vendor,                    # wholesale replacement: carry the vendor binding forward
        ModelBinding(
            kind="custom",
            name="p45b-2rc-ecm (R0 fitted to bench 1C discharge)",
            inline=result.ecm_ps,
            validity=ValidityWindow(
                temperature_celsius=(20.0, 30.0),   # fitted at 25 degC only
                state_of_charge=(0.0, 1.0),
            ),
        ),
    ]
)
save(v7, "p45b.v7.twin.json")
print(v7.version.number, v7.version.changed)
```

Note the narrower validity window: the constant R0 was identified from 25 °C data, so the calibrated binding claims 20–30 °C, not the vendor set's 10–60 °C. Declaring where a model is trusted is exactly what `validity` is for.

```console
$ python fit_model.py
...
7 ['models']

$ battwin validate --shacl p45b.v7.twin.json
ok       p45b.v7.twin.json

$ battwin diff p45b.v6.twin.json p45b.v7.twin.json
versions: 6 -> 7
changed sections: models
version chain: intact (b.previous == hash(a))

$ battwin show p45b.v7.twin.json
Molicel INR2170-P45B (id: urn:bte:molicel-inr2170-p45b:2026-08-10)
  BTE 0.1.1 | version 7 <- sha256:107dad06e4a...
  battinfo record: https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r
  models: p45b-2rc-ecm (About:Energy base set) [custom], p45b-2rc-ecm (R0 fitted to bench 1C discharge) [custom]
  state (2026-08-10): SoC 0%, SoH 95%
  data links: 2
```

The fitted document also carries its own accountability: `fit_thevenin` records the optimiser, the initial and fitted values, the residual, and — because we passed `source_data` — the URI of the dataset it was calibrated against, in the document's `User-defined` section. Anyone holding version 7 can see not just *that* R0 is 18.7 mΩ but *where that number came from*.

## 4. Check the calibration

Rerun the 1C experiment with the fitted binding (exactly as in [Simulate the twin's ECM](simulate-ecm.md), using `v7.models[1]`) and compare all three curves:

```console
vendor set vs measured: RMSE 76.9 mV
fitted set vs measured: RMSE 55.6 mV
```

```{figure} p45b-fit-comparison.png
:alt: Line chart of terminal voltage against time for the 1C discharge at 25 degrees Celsius, with three curves. The measured curve and the fitted model track each other closely through the middle of the discharge, with the vendor parameter set sitting visibly above both. All three converge near the end, where the measured cell reaches cut-off at about 57 minutes while both simulations continue toward 60.
:width: 100%

Measured vs the vendor parameter set vs the calibrated model, for the same 1C discharge. Fitting one parameter against the linked measurement cut the voltage error from 77 to 56 mV RMSE.
```

The calibrated model hugs the measured curve through the bulk of the discharge, where the as-simulated vendor set reads consistently high (that offset is mostly the averaged-OCV projection sitting above the discharge branch the cell actually follows). The remaining error is concentrated at the end-of-discharge knee, and fitting resistance can never fix that part: the knee timing is a *capacity* effect (the measured cell delivered 4.29 Ah against the model's 4.5), which is the same story the twin's SoH snapshot already tells. Each version of this twin has been telling one consistent story from a different angle.

## 5. What you just demonstrated

The full loop, in seven hash-chained documents: the twin was identified from a registry, given a state, bound to an open model, simulated, confronted with measurement, judged (77 mV, SoH 95%), and finally **calibrated to the physical cell it mirrors** — with the generic and fitted models carried side by side, each declaring where it is valid and where its numbers came from. That is the difference between a parameter file and a digital twin: the twin accumulates evidence about one specific battery, verifiably.

For the task-shaped version of fitting, see [Fit ECM parameters](../howto/fit-parameters.md); for the API, [`battwin.fit`](../reference/api.md).
