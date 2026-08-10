# Molicel INR21700-P45B example

An ECM Parameter Set for the Molicel INR21700-P45B cylindrical cell, used by the hands-on tutorials at https://digibatt.github.io/battwin/.

- `molicel-p45b-2rc.ecm-ps.json` — a 2-RC Thevenin equivalent-circuit model in the draft ECM-PS format: topology, sign conventions, cell limits, and column definitions, validated by `battwin.ecm`.
- `molicel-p45b-2rc.params.ecm.csv` — the parameter lookup table the document references: 839 rows over state of charge at 10, 25, 40, and 60 °C.
- `p45b-measured-1c-25degC.bdf.csv` — the release's measured 1C constant-current discharge at 25 °C (`MOLICEL_P45B_025degC_1C_Dch.csv`), converted to BDF column naming with the measurement columns only, as done in the "Link measured data" tutorial.

## Attribution

The parameter values are derived from: About:Energy Ltd, *Data Release — Industry-Standard Parameter Set, Validation Data and Validation Reporting for an Equivalent Circuit Model of the Molicel INR21700-P45B Cylindrical Cell*, Zenodo, DOI [10.5281/zenodo.19052626](https://doi.org/10.5281/zenodo.19052626), licensed CC-BY-4.0. The files here are a format conversion of that release's base parameter set; the values are unchanged. Please cite the dataset DOI if you use these parameters.
