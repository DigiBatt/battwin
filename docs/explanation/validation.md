# How the validation layers fit together

A document conforms to BTE if it validates against the published JSON Schema **and** satisfies the semantic rules of the spec. The reference SDK implements both, plus an optional third layer over the RDF rendering. This page explains what each layer is for and the agreement principle that binds them.

## The three layers

| Layer | Checks | Requires |
|---|---|---|
| JSON Schema (Draft 2020-12) | structure, types, patterns, `format` for date-times and URIs | core install |
| Model rules | cross-field semantics the schema cannot express | core install |
| SHACL shapes | the JSON-LD rendering, as RDF | `battwin[shacl]` |

The schema layer is the language-neutral floor: it is what a Go or JavaScript implementation validates with, so it has to be strict enough to stand alone. The model layer adds what JSON Schema cannot say, such as "exactly one of `source` or `inline`", ordered validity windows, and version-chain rules when a predecessor is available. The SHACL layer exists because envelopes are also RDF documents once rendered as JSON-LD, and some constraints (canonical datetime literals, for instance) are best checked in that world.

## The agreement principle

The layers are designed to agree: the same document must never pass one and fail another for the same underlying reason. Where a check genuinely belongs to one layer, the spec says so explicitly. For example, the JSON Schema's `format: date-time` asserts only that a value is well-formed RFC 3339; the *canonical* UTC-`Z` narrowing of [SPEC §4](../reference/specification.md#4-versioning-and-immutability) is owned by the model layer (which normalizes datetimes when serializing) and, for RDF renderings, by the SHACL layer.

For a format meant to be shared and hashed, the sharp edges are always at boundaries like these: dates that can be written two ways, empty values, keys one checker accepts and another rejects. Treating layer agreement as a design invariant, and red-teaming it before release, is how those edges get caught while they are still cheap.

## Format assertion without dependencies

`format` keywords are asserted, not merely annotated: a malformed `state.as_of` or `identity.battinfo_iri` is reported by the schema layer itself. The assertion stays dependency-free, falling back to lightweight RFC 3339 and URI checks when the `jsonschema[format]` extra is absent and deferring to its stricter native checkers when present.

## In practice

How to actually run the layers, from the CLI and from Python, is the how-to guide [Validate envelope documents](../howto/validate.md). Using the packaged schema from other languages is [Use the contracts outside Python](../howto/contracts.md).
