# battwin documentation

battwin defines the **Battery Twin Envelope (BTE)** — an open specification for
expressing and exchanging battery digital twins as immutable, hash-chained
JSON documents — plus the reference SDK and CLI.

## Sections

- Specification: see [`SPEC.md`](../SPEC.md)
- Installation and Quickstart: see [`README.md`](../README.md)
- JSON Schema: `src/battwin/schemas/twin-envelope.schema.json` (or `battwin schema`)
- JSON-LD context: `src/battwin/context/twin-envelope.context.jsonld` (or `battwin context`)
- SHACL shapes (optional third validation layer, over the JSON-LD rendering):
  `src/battwin/shapes/twin-envelope.shapes.ttl` — install `battwin[shacl]`,
  then `battwin validate --shacl <file>`
- Examples: see [`examples/`](../examples/)
