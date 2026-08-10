# Molicel INR21700-P45B example

Openly licensed model and measurement files for the Molicel INR21700-P45B cylindrical cell, used by the hands-on tutorials at https://digibatt.github.io/battwin/.

- `molicel-p45b-2rc.ecm-ps.json` — a 2-RC Thevenin equivalent-circuit model in the draft ECM-PS 0.2 format (BPX-style sections and parameter names; self-contained, with the lookup grids embedded as 2-D interpolated tables over SoC and temperature). Validated by `battwin.ecm`; runnable via `battwin.sim`.
- `p45b-measured-1c-25degC.bdf.csv` — the release's measured 1C constant-current discharge at 25 °C (`MOLICEL_P45B_025degC_1C_Dch.csv`), converted to BDF column naming with the measurement columns only, as done in the "Link measured data" tutorial.

## Attribution

The parameter values and measurements are derived from: About:Energy Ltd, *Data Release — Industry-Standard Parameter Set, Validation Data and Validation Reporting for an Equivalent Circuit Model of the Molicel INR21700-P45B Cylindrical Cell*, Zenodo, DOI [10.5281/zenodo.19052626](https://doi.org/10.5281/zenodo.19052626), licensed CC-BY-4.0. The ECM-PS file is a format conversion of that release's base parameter set: lookup grids resampled onto the 25 °C SoC axis by linear interpolation so all temperatures share one grid, temperatures converted to Kelvin, values otherwise unchanged. Please cite the dataset DOI if you use these files.
