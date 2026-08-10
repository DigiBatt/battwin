# battwin

**The Battery Twin Envelope (BTE): an open specification, plus a reference SDK and CLI, for expressing and exchanging battery digital twins.**

A battery digital twin is, as a *data artifact*, a composition: an identity, a specification, one or more models, an estimated state, and links to measurement data. Today every platform encapsulates that composition privately. battwin defines it openly, as a small immutable JSON document (the **twin envelope**) that references existing open standards instead of reinventing them:

```
BattINFO records ─────┐  (identity & specification, by IRI)
BPX / BattMo params ──┼──▶  Battery Twin Envelope (.twin.json)  ──▶ registries,
BDF datasets & feeds ─┘  (models & data, by reference)               platforms,
                                                                     archives
```

Envelopes are **documents, not engines**: how a twin is hosted, simulated, or synchronized is an implementation concern; how it is *expressed* is a community concern. The full format is defined in the [specification](reference/specification.md).

## Installation

battwin requires Python 3.10 or newer.

```bash
pip install battwin
```

The core package depends on `pydantic` and `jsonschema`, nothing else. Optional capability lives behind extras, so a bare install never pulls in a solver:

| Extra | Installs | Adds |
|---|---|---|
| `battwin[shacl]` | pyshacl | a third, SHACL-based validation layer over the JSON-LD rendering |
| `battwin[sim]` | PyBaMM | running a twin's equivalent-circuit model as a PyBaMM simulation |
| `battwin[fit]` | PyBOP | fitting a model's parameters against the measured data a twin links |
| `battwin[dev]` | pytest, ruff, mypy | the development toolchain |

## Documentation

The documentation follows the [Diátaxis](https://diataxis.fr/) model: pick the section that matches what you need right now.

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 🎓 Tutorials
:link: tutorials/index
:link-type: doc

Learning-oriented lessons. Start here: create your first twin, validate it, and grow its version chain step by step.
:::

:::{grid-item-card} 🛠 How-to guides
:link: howto/index
:link-type: doc

Task-oriented recipes: validate documents, scaffold from BattINFO, render JSON-LD, run an ECM simulation, verify a chain.
:::

:::{grid-item-card} 📖 Reference
:link: reference/index
:link-type: doc

Information-oriented: the normative BTE specification, the CLI, the full Python API, and the changelog.
:::

:::{grid-item-card} 💡 Explanation
:link: explanation/index
:link-type: doc

Understanding-oriented: why envelopes are documents rather than engines, how immutability and the three validation layers fit together.
:::

::::

## What battwin is not

battwin deliberately does **not** host twins, define sync or REST protocols, manage fleets or tenants, or acquire measurement data (that is [battfeed](https://github.com/DigiBatt/battfeed)'s job). It composes BattINFO, BPX, and BDF by reference rather than replacing them. The [design principles](explanation/design.md) page explains where the lines are drawn and why.

## Related projects

| Project | Role relative to battwin |
|---|---|
| [BattINFO](https://github.com/BIG-MAP/BattINFO) | semantic records the envelope references for identity and specification |
| [BDF / batterydf](https://github.com/battery-data-alliance/battery-data-format) | time-series datasets the envelope links in `data[]` |
| [BPX](https://github.com/FaradayInstitution/BPX) | parameter sets bound in `models[]` |
| [battfeed](https://github.com/DigiBatt/battfeed) | collects live source data into the BDF files a twin links |

## Acknowledgements

```{image} assets/img/Flag_of_Europe.png
:alt: EU flag
:width: 100px
```

This project has received support from European Union research and innovation programs under grant agreement [101103997 – DigiBatt](https://digibattproject.eu/).

battwin is Apache-2.0 licensed. See [LICENSE](https://github.com/DigiBatt/battwin/blob/main/LICENSE) and [NOTICE](https://github.com/DigiBatt/battwin/blob/main/NOTICE).

```{toctree}
:hidden:

tutorials/index
howto/index
reference/index
explanation/index
project/index
```
