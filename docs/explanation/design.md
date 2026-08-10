# Design principles

battwin's design is a small number of deliberate fences. Knowing them makes the rest of the documentation, and the format's omissions, predictable.

## Documents, not engines

The Battery Twin Envelope specifies how a twin is *expressed*, never how it is executed, hosted, or synchronized. Parameter sets have BPX, time-series data has BDF, semantic records have BattINFO; what was missing is the **composition**, one exchangeable object that says *this battery, this specification, these models, this state, this data*. Every platform was reinventing that composition privately. BTE is that layer and only that layer.

This is why the spec's non-goals ([SPEC §7](../reference/specification.md#7-non-goals)) exclude simulation, hosting, sync protocols, fleet management, and data acquisition. Those are implementation concerns, commercial or otherwise; the expression of the twin is a community concern.

## The package is not the format

Two version numbers live in this project and they are not the same thing: the **package** version (what you `pip install`) and the **format** version (the BTE spec). A new package release does not imply a new format revision, and other implementations can target the format without ever touching the Python SDK. The same doctrine governed the naming: the package is battwin, the format is BTE, just as `batterydf` is a package and BDF is a format.

It is also why the reference SDK can ship conveniences the spec never mentions. The `battwin[sim]` extra runs an equivalent-circuit model in PyBaMM, but the *format* still says nothing about execution; everything the extra computes flows back into the envelope as ordinary spec objects (data links, state snapshots) through `next_version()`. The runtime serves the format, never bypasses it.

## Reference, don't copy

An envelope points at BattINFO records, BPX parameter files, and BDF datasets by their address; it does not paste their contents in (an `inline` model payload is the pragmatic exception, for parameter sets that have no stable address). Composition by reference keeps the envelope small, keeps each referenced standard authoritative for its own content, and means an envelope never goes stale relative to the record it cites: it cites exactly the thing it cited.

## Immutability over mutability

Envelopes are frozen at creation, in the spec and in the SDK's models alike. The reasons, and the hash-chain mechanics that follow from them, get their own page: [versioning and immutability](versioning.md).

## Lean core, optional extras

A bare `pip install battwin` brings exactly two dependencies, `pydantic` and `jsonschema`. Everything else (SHACL validation, PyBaMM simulation) lives behind extras, and a missing extra fails with an actionable "install battwin[X]" message rather than an import error. A contract library that everyone is meant to depend on cannot afford a heavy dependency tree.

## Everyone must agree

Three validation layers check the same documents ([how they fit together](validation.md)), and the published JSON Schema must be strict enough to stand alone, because non-Python implementations validate with it and nothing else. A document must never pass one layer and fail another for the same underlying reason; where a check cannot be expressed in one layer, the spec says explicitly which layer owns it.
