# battwin

**The Battery Twin Envelope (BTE): an open specification, plus a reference SDK and CLI, for expressing and exchanging battery digital twins.**

A battery digital twin is, as a *data artifact*, a composition: an identity, a specification, one or more models, an estimated state, and links to measurement data. Today every platform encapsulates that composition privately. battwin defines it openly, as a small immutable JSON document (the **twin envelope**) that references existing open standards instead of reinventing them:

```
BattINFO records ─────┐  (identity & specification, by IRI)
BPX / BattMo params ──┼──▶  Battery Twin Envelope (.twin.json)  ──▶ registries,
BDF datasets & feeds ─┘  (models & data, by reference)               platforms,
                                                                     archives
```

Envelopes are **documents, not engines**: how a twin is hosted, simulated, or synchronized is an implementation concern; how it is *expressed* is a community concern. The full format is defined in the [specification](spec.md).

## In thirty seconds

```bash
pip install battwin
```

```python
from battwin import new_envelope, save, validate_file

twin = new_envelope(label="Bench cell 001", chemistry="LFP")
save(twin, "bench-cell-001.twin.json")
assert validate_file("bench-cell-001.twin.json") == []
```

Updating a twin never mutates it. Each update is a new document whose `version.previous` field holds the content hash of its predecessor, so any consumer can verify the lineage. The [versioning guide](guide/versioning.md) walks through the chain.

## Where to go next

<div class="grid cards" markdown>

-   :material-rocket-launch-outline: **[Getting started](getting-started.md)**

    Install the package, create your first envelope from Python or the command line, and understand the optional extras.

-   :material-file-document-outline: **[The twin envelope](guide/envelope.md)**

    A guided tour of every section of a `.twin.json` document, with a complete worked example.

-   :material-book-open-variant: **[Specification](spec.md)**

    The normative BTE format definition: document model, versioning rules, conformance, and JSON-LD rendering.

-   :material-code-braces: **[API reference](api.md)**

    The full Python API: envelope models, I/O, validation, BattINFO helpers, ECM parameter sets, and simulation.

</div>

## What battwin is not

battwin deliberately does **not** host twins, define sync or REST protocols, manage fleets or tenants, or acquire measurement data (that is [battfeed](https://github.com/DigiBatt/battfeed)'s job). It composes BattINFO, BPX, and BDF by reference rather than replacing them. The reference SDK does ship an optional [`battwin[sim]` extra](guide/ecm-sim.md) that can run a twin's equivalent-circuit model in PyBaMM as a convenience, but the *format* never specifies execution.

## Related projects

| Project | Role relative to battwin |
|---|---|
| [BattINFO](https://github.com/BIG-MAP/BattINFO) | semantic records the envelope references for identity and specification |
| [BDF / batterydf](https://github.com/battery-data-alliance/battery-data-format) | time-series datasets the envelope links in `data[]` |
| [BPX](https://github.com/FaradayInstitution/BPX) | parameter sets bound in `models[]` |
| [battfeed](https://github.com/DigiBatt/battfeed) | collects live source data into the BDF files a twin links |

## Acknowledgements

<img src="assets/img/Flag_of_Europe.png" alt="EU flag" width="100">

This project has received support from European Union research and innovation programs under grant agreement [101103997 – DigiBatt](https://digibattproject.eu/).

battwin is Apache-2.0 licensed. See [LICENSE](https://github.com/DigiBatt/battwin/blob/main/LICENSE) and [NOTICE](https://github.com/DigiBatt/battwin/blob/main/NOTICE).
