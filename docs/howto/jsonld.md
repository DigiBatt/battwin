# Render an envelope as JSON-LD

Every conforming envelope also renders as JSON-LD, so twins slot into linked-data pipelines alongside BattINFO records without a transformation service.

## From Python

```python
from battwin import load, save

env = load("cell.twin.json")
save(env, "cell.jsonld.twin.json", jsonld=True)
```

## From the command line

Write JSON-LD directly when scaffolding:

```bash
battwin init --label "Bench cell 001" --jsonld -o cell.twin.json
```

## What the rendering adds

Three keys turn a conforming document into JSON-LD: `"@context"` (the context published with the spec), `"@id"` (equal to `id`), and `"@type": "TwinEnvelope"`. The context maps identity fields to schema.org terms and domain terms to the `bte:` prefix, with BattINFO IRIs as first-class references.

To use the context in another toolchain, print it:

```bash
battwin context > twin-envelope.context.jsonld
```

```{admonition} Term IRIs are provisional
:class: warning

The `/twin` redirect rules are not yet part of the battinfo w3id registration, so the term IRIs do not dereference yet. See [namespaces and linked data](../explanation/linked-data.md).
```

## Validate the RDF rendering

With the `battwin[shacl]` extra installed, `battwin validate --shacl` checks the JSON-LD rendering against the packaged SHACL shapes; see [Validate envelope documents](validate.md).
