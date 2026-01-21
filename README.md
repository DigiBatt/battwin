# echoed

A modular digital twin framework for batteries and electrochemical systems. Echoed connects models, data, and metadata into a living, updatable representation of a physical cell or system. It builds on open ontologies and interoperable formats, so that experimental data, simulations, and analytics can all flow into the same consistent digital twin.

---

## Features

- **Battery-focused digital twins** – model full cells, electrodes, and materials across scales.
- **Interoperable by design** – built on [cold](https://github.com/your-org/cold), [pybop](https://github.com/your-org/pybop), [pybamm](https://github.com/pybamm-team/pybamm), [BattMo](https://github.com/BattMo/battmo).
- **Linked data integration** – RDF/JSON-LD backbone, based on the EMMO and battery domain ontologies.
- **Flexible composition** – connect test data, parameters, and models into a unified instance.
- **Continuous synchronization** – update the twin when new measurements or simulations arrive.
- **Extensible workflows** – plug in your own solvers, optimizers, or analysis tools.
- **Human + machine interfaces** – Python API, REST/GraphQL endpoints (planned), and rich visualization.

---

## Installation

Clone the repository. Install the package in editable mode.

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dev,bdf,viz]"
```

## BDF data (preview)

Echoed includes a small ingestion helper to load Battery Data Format (BDF) assets.
Install the `bdf` extra and use `echoed.data.load_bdf` to bring datasets into
your workflows.

### Acknowledgements

<img src="docs/assets/img/Flag_of_Europe.png" alt="EU-Flag" width="100">

This project has received support from European Union research and innovation programs, under grant agreement numbers:

* [101103997 - DigiBatt](https://digibattproject.eu/)
