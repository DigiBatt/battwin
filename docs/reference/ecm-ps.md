# ECM-PS format

The **ECM Parameter Set (ECM-PS)** is battwin's draft format for equivalent-circuit-model parameters: the payload a twin's model binding carries when the model is an ECM rather than a physics parameter set. This page describes draft **0.2**; the packaged JSON Schema (`battwin/schemas/ecm-params.schema.json`, validated by [`battwin.ecm`](api.md)) is the precise definition.

## Design premise: BPX style, ECM content

[BPX](https://github.com/FaradayInstitution/BPX) is the established exchange format for physics-based battery models (SPM, SPMe, DFN), but it defines no ECM model type, and industry ECM releases consequently ship as ad-hoc CSVs. ECM-PS fills that gap **in BPX's own idiom**, so the two formats stay as interoperable as possible and ECM-PS could fold into BPX if it ever adopts an ECM model type:

- the same top-level sections: `Header`, `Parameterisation`, `State`, `Validation`;
- the same naming convention: natural-language parameter names with bracketed SI units in dot notation (`"R0 [Ohm]"`, `"Entropic change [V.K-1]"`); dimensionless names carry no bracket;
- the same value idiom: a parameter is a constant or an interpolated table (`{"x": [...], "y": [...]}`), extended with a minimal 2-D form for the (SoC, temperature) grids that measured ECM parameters actually come as;
- the same SI discipline: temperatures in Kelvin;
- conventions fixed by the spec rather than declared per file: SoC is a 0–1 fraction, and there are no executable expression strings (documents, not engines — a deliberate divergence from BPX, whose physics parameters may be math-expression strings).

A `Header` field distinguishes the formats honestly: an ECM-PS file declares `"ECM-PS version"`, never a `"BPX"` version, so it cannot falsely claim BPX conformance.

## Document structure

```json
{
  "Header": {
    "ECM-PS version": "0.2",
    "Model": "ECM",
    "Title": "...",
    "Description": "...",
    "References": ["...dataset DOI..."],
    "BattINFO record": "https://w3id.org/battinfo/spec/..."
  },
  "Parameterisation": {
    "Cell": {
      "Nominal cell capacity [A.h]": 4.5,
      "Lower voltage cut-off [V]": 2.5,
      "Upper voltage cut-off [V]": 4.2,
      "Reference temperature [K]": 298.15,
      "Number of RC elements": 2
    },
    "Circuit": {
      "Open-circuit voltage on charge [V]":    { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "Open-circuit voltage on discharge [V]": { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "Hysteresis decay rate":                 { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "R0 [Ohm]": { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "R1 [Ohm]": { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "C1 [F]":   { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "R2 [Ohm]": { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "C2 [F]":   { "x": ["..."], "y": ["..."], "z": [["..."]] },
      "Entropic change [V.K-1]": { "x": ["..."], "y": ["..."], "z": [["..."]] }
    },
    "User-defined": { }
  },
  "State": { "Initial SoC": 1.0, "Initial temperature [K]": 298.15 },
  "Validation": { }
}
```

`Header` and `Parameterisation` are required; `State`, `Validation`, and `User-defined` are optional. `Circuit` requires `R0 [Ohm]` plus either a single `Open-circuit voltage [V]` or both hysteresis branches, and must define `R{i} [Ohm]` / `C{i} [F]` for every branch up to `Number of RC elements`. Unknown Circuit names are invalid; anything vendor-specific belongs in `User-defined` — for example, [`battwin.fit`](../howto/fit-parameters.md) records its fit provenance there under the `"pybop"` key.

## Values

A parameter value is one of:

| Form | Meaning |
|---|---|
| number | a constant |
| `{"x": [...], "y": [...]}` | 1-D interpolation; `x` is a strictly increasing SoC grid |
| `{"x": [...], "y": [...], "z": [[...]]}` | 2-D interpolation; `x` = SoC grid, `y` = temperature grid [K], `z[i][j]` = value at `y[i]`, `x[j]` |

## Semantics and PyBaMM mapping

Semantic grounding lives at spec level rather than per file: each defined parameter name maps to a class in the EMMO domain-equivalent-circuit-model ontology, and the schema's description fields carry the exact PyBaMM parameter each name exports to (`"R0 [Ohm]"` → `R0 [Ohm]`, `"Entropic change [V.K-1]"` → `Entropic change [V/K]`, and so on). The optional `Header` field `BattINFO record` links the parameter set to the same registry record a twin references, which is what lets tooling confirm that a twin and its model describe the same cell. The schema `$id` under the EMMO domain namespace is provisional until the corresponding w3id redirects are registered.

## Validating and running

```python
from battwin.ecm import validate_ecm_ps_file      # core install: validation only
from battwin.sim import build_thevenin            # battwin[sim]: execution

assert validate_ecm_ps_file("cell.ecm-ps.json") == []
```

See [Run an ECM simulation](../howto/run-ecm.md) for the execution side, and [`examples/p45b/`](https://github.com/DigiBatt/battwin/tree/main/examples/p45b) for a complete real-world document (the About:Energy Molicel INR21700-P45B release, converted).

## Relationship to the twin envelope

An ECM-PS attaches to a twin as an ordinary model binding (`kind: "custom"` until BTE 0.2 decides whether `"ecm"` joins the enum), with the document `inline` or behind `source`. The envelope declares *which* model applies and *when it is valid*; the ECM-PS carries the parameters; execution stays a consumer concern.
