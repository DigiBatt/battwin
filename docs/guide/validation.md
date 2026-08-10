# Validation

A document conforms to BTE if it validates against the published JSON Schema **and** satisfies the semantic rules of the spec (exactly one of `source`/`inline` per model binding, ordered validity windows, version-chain rules when a predecessor is available, and so on). The reference SDK implements both, plus an optional third layer over the RDF rendering.

## The three layers

| Layer | Checks | Requires |
|---|---|---|
| JSON Schema (Draft 2020-12) | structure, types, patterns, `format` for date-times and URIs | core install |
| Model rules | cross-field semantics the schema cannot express | core install |
| SHACL shapes | the JSON-LD rendering, as RDF | `battwin[shacl]` |

The layers are designed to agree: the same document must never pass one and fail another for the same reason. The JSON Schema is deliberately strict enough to stand alone, because non-Python tools validate with it and nothing else.

## From the command line

```console
$ battwin validate cell.twin.json broken.twin.json
ok       cell.twin.json
INVALID  broken.twin.json
  - $.models[0]: exactly one of 'source' or 'inline' is required
```

`battwin validate` accepts multiple files and exits `1` if any is invalid. Add `--shacl` to also run the packaged SHACL shapes (exits `2` with a clear message if the `battwin[shacl]` extra is not installed).

## From Python

```python
from battwin import validate_file, validate_dict

problems = validate_file("cell.twin.json")           # list[str], empty = valid
problems = validate_dict(doc)                        # same, for a parsed dict
problems = validate_dict(doc, shacl=True)            # include the SHACL layer
```

Both functions return all problems from all requested layers rather than stopping at the first, so one pass tells you everything that is wrong.

## Schema `format` assertion

`format: date-time` and `format: uri` are asserted, not just annotated: a malformed `state.as_of` or `identity.battinfo_iri` is reported by the schema layer itself. The assertion stays dependency-free, falling back to lightweight RFC 3339 and URI checks when the `jsonschema[format]` extra is absent and deferring to its stricter native checkers when present. The canonical UTC-`Z` datetime narrowing of [SPEC §4](../spec.md#4-versioning-and-immutability) is enforced by the model layer (which normalizes datetimes when serializing) and, for RDF renderings, by the SHACL layer.

## Using the contracts outside Python

The three artifacts ship inside the package and are the same files any other implementation should validate against:

- JSON Schema: `battwin/schemas/twin-envelope.schema.json`, or `battwin schema`
- JSON-LD context: `battwin/context/twin-envelope.context.jsonld`, or `battwin context`
- SHACL shapes: `battwin/shapes/twin-envelope.shapes.ttl`

In Python they load as plain objects too: `load_schema()`, `load_context()`, `load_shapes()`.

## ECM parameter sets

battwin also packages a draft JSON Schema for ECM Parameter Set documents and small helpers to validate them (`battwin.ecm`). That is covered in the [ECM models and simulation guide](ecm-sim.md).
