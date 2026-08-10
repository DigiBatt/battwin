# Versioning and hashing

Envelope documents are **immutable**. Once written, a `.twin.json` file never changes; updating a twin means issuing a new document that points back at the old one by content hash. That gives every twin a verifiable history: any consumer, in any language, can check that a claimed successor really derives from its predecessor.

## The content hash

The hash of an envelope is

```
"sha256:" + hex(sha256(canonical_json))
```

where `canonical_json` serializes the document with sorted keys, `(",", ":")` separators, UTF-8, and all null-valued fields omitted. In the canonical form, all datetimes are RFC 3339 UTC with a `Z` suffix (offsets normalized to UTC, fractional seconds without trailing zeros), so the same instant always hashes the same way. `load(save(env))` is a content-hash fixed point.

```python
from battwin import load

env = load("cell.twin.json")
print(env.content_hash())   # sha256:3f7a...
```

Or from the shell: `battwin hash cell.twin.json`.

## Issuing a new version

`next_version()` produces the successor document. Each keyword argument replaces that top-level section **wholesale** (there is no merging), and the version record is maintained for you:

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

assert v2.id == v1.id                              # same twin
assert v2.version.number == v1.version.number + 1  # incremented
assert v2.version.previous == v1.content_hash()    # chained
assert v2.version.changed == ["state"]             # what moved
save(v2, "cell.v2.twin.json")
```

When a new snapshot replaces `state`, the previous snapshot is carried into `state_history`, so nothing is lost by the wholesale replacement.

## Verifying a chain

`battwin diff` compares two documents and checks the link:

```console
$ battwin diff cell.twin.json cell.v2.twin.json
versions: 1 -> 2
changed sections: state
version chain: intact (b.previous == hash(a))
```

It exits `0` when the chain is intact and `1` when the documents belong to different twins or `b.version.previous` does not equal the hash of `a`. In Python, the same check is one comparison: `b.version.previous == a.content_hash()`.

## Why immutability

A twin's state estimates feed downstream decisions (warranties, second-life assessment, passports), so "what did the twin say, and when" has to be answerable later. Hash chaining makes the answer verifiable rather than trusted: tampering with any historical document breaks every hash after it. The pattern is proven in production twin platforms; BTE standardizes the shape, not the platform.
