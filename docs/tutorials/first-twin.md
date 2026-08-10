# Your first twin: a Molicel P45B

In this tutorial you will build a battery digital twin of a real cell, the Molicel INR21700-P45B, from its live BattINFO registry record. You will look inside the envelope, validate it, update it with a state estimate, verify the version chain that update creates, and then tamper with history to watch the chain break.

The outputs shown are from a real run of every command (2026-08-10, battwin 0.4.0). Your timestamps and hashes will differ; everything else should look the same.

You need Python 3.10 or newer, network access (step 2 dereferences the registry), and about fifteen minutes.

## 1. Install battwin

```bash
pip install battwin
```

```console
$ battwin --version
battwin 0.4.0
```

## 2. Twin the cell from its registry record

The P45B has a record in the BattINFO registry. Instead of typing its identity by hand, scaffold the envelope straight from the record's IRI:

```console
$ battwin init --from-battinfo https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r --created-by "Simon Clark" -o p45b.twin.json
wrote p45b.twin.json
```

Here is the entire file that produced. This document *is* the twin, as far as exchange is concerned:

```json
{
  "bte_version": "0.1.1",
  "id": "urn:bte:molicel-inr2170-p45b:2026-08-10",
  "identity": {
    "label": "Molicel INR2170-P45B",
    "manufacturer": "Molicel",
    "model": "INR2170-P45B"
  },
  "specification": {
    "battinfo_record": "https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r"
  },
  "models": [],
  "state_history": [],
  "data": [],
  "provenance": {
    "created": "2026-08-10T14:58:15.637524Z",
    "created_by": "Simon Clark",
    "tool": "battwin/0.4.0"
  },
  "version": {
    "number": 1,
    "changed": [],
    "timestamp": "2026-08-10T14:58:15.637524Z"
  }
}
```

Notice what the helper did and did not do: `identity` was seeded from the record (label, manufacturer, model), and `specification` carries the record's IRI as a *reference*, not a copy. The registry record for the P45B is currently sparse (no chemistry or capacity in its specs), so those convenience fields are simply absent rather than guessed.

```{admonition} No network?
:class: tip

`battwin init --label "Molicel INR21700-P45B" --chemistry NMC -o p45b.twin.json` scaffolds an equivalent envelope offline; the rest of the tutorial works identically.
```

## 3. Inspect, validate, hash

```console
$ battwin show p45b.twin.json
Molicel INR2170-P45B (id: urn:bte:molicel-inr2170-p45b:2026-08-10)
  BTE 0.1.1 | version 1
  battinfo record: https://w3id.org/battinfo/spec/ycek-4qa3-d4v3-rm6r

$ battwin validate p45b.twin.json
ok       p45b.twin.json

$ battwin hash p45b.twin.json
sha256:4781f1a43fcaec987bf49a775c3252450901656206ac4f8c5ed660e147a62ca6
```

That hash is the document's fingerprint: SHA-256 over the canonical serialization. Remember it; it is about to reappear.

## 4. Update the twin with a state estimate

Suppose you have just commissioned this cell at the bench: charged it full with a CC-CV protocol and let it rest. Record that as the twin's state. Envelopes are immutable, so this means issuing a *new* document. Save this as `update_state.py`:

```python
from datetime import datetime, timezone
from battwin import StateSnapshot, load, save

v1 = load("p45b.twin.json")
v2 = v1.next_version(
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=1.0,
        state_of_health=1.0,
        cycle_count=0,
        method="cc-cv charge to 4.2 V, C/50 cut-off, 1 h rest",
    )
)
save(v2, "p45b.v2.twin.json")
print(v2.version.number, v2.version.changed)
```

```console
$ python update_state.py
2 ['state']
```

Open `p45b.v2.twin.json` and look at its `state` and `version` sections:

```json
{
  "state": {
    "as_of": "2026-08-10T14:59:36.481242Z",
    "state_of_charge": 1.0,
    "state_of_health": 1.0,
    "cycle_count": 0,
    "method": "cc-cv charge to 4.2 V, C/50 cut-off, 1 h rest"
  },
  "version": {
    "number": 2,
    "previous": "sha256:4781f1a43fcaec987bf49a775c3252450901656206ac4f8c5ed660e147a62ca6",
    "changed": ["state"],
    "timestamp": "2026-08-10T14:59:36.481242Z"
  }
}
```

`version.previous` is exactly the hash you printed in step 3. You never computed or copied it; `next_version()` chained the documents for you.

## 5. Verify the chain

Check the lineage from the outside, the way any consumer would:

```console
$ battwin diff p45b.twin.json p45b.v2.twin.json
versions: 1 -> 2
changed sections: state
version chain: intact (b.previous == hash(a))
```

## 6. Tamper with history and watch it break

Now the payoff. Edit `p45b.twin.json` and change one field, say `created_by` from `Simon Clark` to `Someone Else` (or change any other character). Then diff again:

```console
$ battwin diff p45b.twin.json p45b.v2.twin.json
versions: 1 -> 2
changed sections: provenance, state
version chain: BROKEN (b.previous != hash(a))
```

One character changed anywhere in v1 and the chain no longer verifies (the command also exits `1`, so scripts catch it too). That tamper-evidence is the point of the design: a twin's history is not something you are asked to trust, it is something you can check. Undo your edit before continuing.

## 7. Where you are now

You have a twin of a real, registry-identified cell with a verifiable two-version history. In the next tutorial the same twin gets an open equivalent-circuit model and is simulated in PyBaMM, with the results committed as versions 3 and 4 of this same chain: [Simulate the twin's ECM](simulate-ecm.md).

For the ideas behind what you just did, see [versioning and immutability](../explanation/versioning.md) and [anatomy of an envelope](../explanation/envelope.md).
