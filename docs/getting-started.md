# Getting started

## Installation

battwin requires Python 3.10 or newer.

```bash
pip install battwin
```

The core package depends on `pydantic` and `jsonschema`, nothing else. Optional capability lives behind extras, so a bare install never pulls in a solver:

| Extra | Installs | Adds |
|---|---|---|
| `battwin[shacl]` | pyshacl | a third, SHACL-based validation layer over the JSON-LD rendering ([validation guide](guide/validation.md)) |
| `battwin[sim]` | PyBaMM | running a twin's equivalent-circuit model as a PyBaMM Thevenin simulation ([ECM guide](guide/ecm-sim.md)) |
| `battwin[dev]` | pytest, ruff, mypy | the development toolchain ([development guide](development.md)) |

```bash
pip install "battwin[shacl]"        # extras compose: "battwin[shacl,sim]"
```

## Your first envelope, from Python

```python
from battwin import new_envelope, save, validate_file

twin = new_envelope(label="Bench cell 001", chemistry="LFP")
save(twin, "bench-cell-001.twin.json")
assert validate_file("bench-cell-001.twin.json") == []
```

`new_envelope` scaffolds a minimal valid document: an identity with your label, a generated `urn:bte:` identifier, provenance, and version number 1. `save` writes the canonical JSON form; `validate_file` returns a list of problems, empty when the document conforms.

Updating a twin creates a new, hash-chained version, because envelopes are immutable:

```python
from datetime import datetime, timezone
from battwin import StateSnapshot, load, save

v1 = load("bench-cell-001.twin.json")
v2 = v1.next_version(
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=0.8,
        method="coulomb_counting",
        source_data="data/SINTEF__001__20260707_001.bdf.csv",
    )
)
assert v2.version.previous == v1.content_hash()  # verifiable lineage
save(v2, "bench-cell-001.v2.twin.json")
```

## Your first envelope, from the command line

```bash
battwin init --label "Bench cell 001" --chemistry LFP -o cell.twin.json
battwin validate cell.twin.json
battwin show cell.twin.json
```

If the cell you are twinning already has a BattINFO registry record, you can seed the envelope straight from its IRI instead of typing the identity by hand:

```bash
battwin init --from-battinfo https://w3id.org/battinfo/spec/<id> -o cell.twin.json
```

See the [BattINFO integration guide](guide/battinfo.md) for what gets mapped, and the [CLI reference](guide/cli.md) for every command and exit code.

## The contracts, without Python

The JSON Schema, JSON-LD context, and SHACL shapes ship inside the package, and the CLI prints the first two to stdout so non-Python consumers can pull the language-neutral contracts without touching the SDK:

```bash
battwin schema   > twin-envelope.schema.json
battwin context  > twin-envelope.context.jsonld
```

## Reading order

1. [The twin envelope](guide/envelope.md): what each section of the document means.
2. [Versioning and hashing](guide/versioning.md): immutability, the content hash, and the version chain.
3. [Validation](guide/validation.md): the three checking layers and how to run them.
4. [Specification](spec.md): the normative definition, when you need the exact rules.
