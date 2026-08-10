# Your first twin

In this tutorial you will create a battery twin envelope, look inside it, validate it, update it with a state estimate, and verify the version chain that update creates. At the end you will have a two-document twin history whose integrity you can prove.

You need Python 3.10 or newer and about ten minutes.

## 1. Install battwin

```bash
pip install battwin
```

Check the install:

```console
$ battwin --version
battwin 0.4.0
```

## 2. Create an envelope

Ask battwin to scaffold a minimal valid document for a bench cell:

```console
$ battwin init --label "Bench cell 001" --chemistry LFP -o cell.twin.json
wrote cell.twin.json
```

Open `cell.twin.json` in your editor. You will find a small JSON object: an `identity` carrying your label, a generated `urn:bte:` identifier, a `specification` with the chemistry, `provenance` saying when and by what the document was made, and a `version` record at number 1. That object *is* the twin, as far as exchange is concerned.

## 3. Inspect and validate it

```console
$ battwin show cell.twin.json
```

prints a human-readable summary. More importantly:

```console
$ battwin validate cell.twin.json
ok       cell.twin.json
```

`validate` checks the document against the packaged JSON Schema and the spec's semantic rules. Try breaking it: edit the file, change `"bte_version"` to `"9.9.9"`, and validate again. You get an `INVALID` line with the specific problem. Undo your edit (or just regenerate the file) before continuing.

## 4. Update the twin with a state estimate

Envelopes are immutable, so "updating" means issuing a new document that points back at the old one. Do it from Python:

```python
from datetime import datetime, timezone
from battwin import StateSnapshot, load, save

v1 = load("cell.twin.json")
v2 = v1.next_version(
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=0.8,
        method="coulomb_counting",
    )
)
save(v2, "cell.v2.twin.json")
print(v2.version.number, v2.version.changed)
```

Run it:

```console
$ python update.py
2 ['state']
```

Two things happened. The new document's `version.number` incremented, and its `version.previous` field was set to the **content hash** of `v1`, a SHA-256 over the canonical serialization. You never computed that hash; `next_version()` did.

## 5. Verify the chain

Now prove the lineage from the outside, the way any consumer would:

```console
$ battwin diff cell.twin.json cell.v2.twin.json
versions: 1 -> 2
changed sections: state
version chain: intact (b.previous == hash(a))
```

The chain is intact because hashing `cell.twin.json` reproduces exactly the value stored in `cell.v2.twin.json`. Edit even one character of the v1 file and `diff` will report the chain as broken; that tamper-evidence is the point of the design.

## 6. Where you are now

You have a twin with a verifiable two-version history, produced and checked entirely with open tooling. From here:

- [Simulate a twin's ECM](simulate-ecm.md) continues the story into models and simulation.
- The [how-to guides](../howto/index.md) cover single tasks, like scaffolding from a BattINFO record or rendering JSON-LD.
- [Versioning and immutability](../explanation/versioning.md) explains *why* the format works this way.
