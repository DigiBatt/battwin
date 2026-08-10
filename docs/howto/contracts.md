# Use the contracts outside Python

BTE is language-neutral: the JSON Schema, JSON-LD context, and SHACL shapes are the contracts, and any implementation should validate against the same files the reference SDK ships.

## Get the files

With battwin installed, print them:

```bash
battwin schema   > twin-envelope.schema.json
battwin context  > twin-envelope.context.jsonld
```

Or take them straight from the package source:

- JSON Schema (Draft 2020-12): [`src/battwin/schemas/twin-envelope.schema.json`](https://github.com/DigiBatt/battwin/blob/main/src/battwin/schemas/twin-envelope.schema.json)
- JSON-LD context: [`src/battwin/context/twin-envelope.context.jsonld`](https://github.com/DigiBatt/battwin/blob/main/src/battwin/context/twin-envelope.context.jsonld)
- SHACL shapes: [`src/battwin/shapes/twin-envelope.shapes.ttl`](https://github.com/DigiBatt/battwin/blob/main/src/battwin/shapes/twin-envelope.shapes.ttl)
- ECM-PS JSON Schema: [`src/battwin/schemas/ecm-params.schema.json`](https://github.com/DigiBatt/battwin/blob/main/src/battwin/schemas/ecm-params.schema.json)

## What schema validation alone gives you

The JSON Schema is deliberately strict enough to stand on its own: structure, types, key grammars, and asserted `format` checks for date-times and URIs. Full conformance additionally requires the semantic rules of [SPEC §5](../reference/specification.md#5-validation-and-conformance) (exactly one of `source`/`inline` per model binding, ordered validity windows, version-chain rules), which a non-Python implementation must apply itself.

## Reproduce the content hash

The hash needs no battwin code: serialize with sorted keys, `(",", ":")` separators, UTF-8, null-valued fields omitted, datetimes in canonical UTC-`Z` form, then `"sha256:" + hex(sha256(bytes))`. The normative definition is [SPEC §4](../reference/specification.md#4-versioning-and-immutability).
