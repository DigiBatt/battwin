# Molicel INR21700-P45B example

Openly licensed model and measurement files for the Molicel INR21700-P45B cylindrical cell, used by the hands-on tutorials at https://digibatt.github.io/battwin/.

- `molicel-p45b-2rc.ecm-ps.json` — a 2-RC Thevenin equivalent-circuit model in the draft ECM-PS 0.2 format (BPX-style sections and parameter names; self-contained, with the lookup grids embedded as 2-D interpolated tables over SoC and temperature). Validated by `battwin.ecm`; runnable via `battwin.sim`.
- `p45b-measured-1c-25degC.bdf.csv` — the release's measured 1C constant-current discharge at 25 °C (`MOLICEL_P45B_025degC_1C_Dch.csv`), converted to BDF column naming with the measurement columns only, as done in the "Link measured data" tutorial.

## Attribution

The parameter values and measurements are derived from: About:Energy Ltd, *Data Release — Industry-Standard Parameter Set, Validation Data and Validation Reporting for an Equivalent Circuit Model of the Molicel INR21700-P45B Cylindrical Cell*, Zenodo, DOI [10.5281/zenodo.19052626](https://doi.org/10.5281/zenodo.19052626), licensed CC-BY-4.0. The ECM-PS file is a format conversion of that release's base parameter set: lookup grids resampled onto the 25 °C SoC axis by linear interpolation so all temperatures share one grid, temperatures converted to Kelvin, values otherwise unchanged. Please cite the dataset DOI if you use these files.

The model, characterisation, and validation behind the release are described in the accompanying paper: E. J. F. Dickinson, C. Zor, D. Doyle, C. Pilling, K. Lukow, K. O'Regan, M. Blyth, A. Hales, and G. White, *An Industry-Standard Parameterisation of a Lithium-Ion Battery Equivalent Circuit Model for a High-Power Cylindrical Cell: Molicel P45B*, preprint (under review), [SSRN 6861858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6861858). Both citations are carried machine-readably in the ECM-PS file's `Header.References`.

One fidelity note for users of the ECM-PS file with `battwin[sim]`: the source model uses Plett one-state OCV hysteresis (both branches and the decay rate are preserved in this file), while PyBaMM's basic Thevenin has a single OCV, so `battwin.sim` averages the branches. On this cell the branch half-gap averages ~29 mV over SoC ≥ 10%, so simulations of monotonic discharges read correspondingly high; with the discharge branch substituted as the single OCV, `battwin.sim` reproduces the paper's 25 °C 1C validation error (17.3 mV RMS down to 10% SoC) exactly.
