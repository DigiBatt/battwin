# Versioning and immutability

Envelope documents are **immutable**. Once written, a `.twin.json` file never changes; updating a twin means issuing a new document that points back at the old one by content hash. This page explains the mechanism and the reasoning.

## Why immutability

A twin's state estimates feed downstream decisions: warranties, second-life assessment, battery passports. For all of those, "what did the twin say, and when" has to be answerable later, and answerable in a way that does not depend on trusting whoever stored the files. Hash chaining makes the answer *verifiable*: tampering with any historical document changes its hash and breaks every link after it. The pattern is proven in production twin platforms; BTE standardizes the shape, not the platform.

## The content hash

The hash of an envelope is

```
"sha256:" + hex(sha256(canonical_json))
```

where `canonical_json` serializes the document with sorted keys, `(",", ":")` separators, UTF-8, and all null-valued fields omitted. Canonicalization is what makes the hash meaningful across implementations: the same information must always produce the same bytes. The subtlest part is datetimes, which JSON lets you write many ways; in the canonical form they are always RFC 3339 UTC with a `Z` suffix, offsets normalized, fractional seconds without trailing zeros. A consequence worth knowing: `load(save(env))` is a content-hash fixed point.

## How a new version is issued

`next_version()` produces the successor. Each keyword argument replaces that top-level section **wholesale**, and the version record is maintained for you:

```python
v2 = v1.next_version(state=StateSnapshot(...))

assert v2.id == v1.id                              # same twin
assert v2.version.number == v1.version.number + 1  # incremented
assert v2.version.previous == v1.content_hash()    # chained
assert v2.version.changed == ["state"]             # what moved
```

Wholesale replacement, rather than merging, is deliberate: merge semantics are where document formats grow ambiguity, and an envelope is small enough that replacing a section costs nothing. Nothing is lost by it either, because a replaced `state` snapshot is carried into `state_history`.

## Verifying

Verification is one comparison per link: `b.version.previous == a.content_hash()`. The CLI wraps it as `battwin diff`, and any language can reproduce it from the canonical-form rules alone. The task-shaped walkthrough is [Verify a twin's version chain](../howto/verify-chain.md); the normative rules are [SPEC §4](../reference/specification.md#4-versioning-and-immutability).
