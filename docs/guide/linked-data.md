# Linked data

Every conforming envelope also renders as JSON-LD, so twins slot into linked-data pipelines alongside BattINFO records without any transformation service.

## Rendering an envelope as JSON-LD

Adding `"@context"` (the context published with the spec), `"@id"` (equal to `id`), and `"@type": "TwinEnvelope"` to a conforming document yields JSON-LD. The SDK does this for you:

```python
from battwin import load, save

env = load("cell.twin.json")
save(env, "cell.jsonld.twin.json", jsonld=True)
```

The CLI equivalent is `battwin init --jsonld`, and `battwin context` prints the packaged context for use in other toolchains.

The context maps identity fields to schema.org terms and domain terms to the `bte:` prefix, with BattINFO IRIs as first-class references.

## Namespace policy: BattINFO owns the names

BTE deliberately introduces **no new namespace**. BattINFO (`https://w3id.org/battinfo`, a registered w3id namespace) is the authority for battery-related IRIs, and BTE terms live under it:

- vocabulary terms: `https://w3id.org/battinfo/twin#` (the `bte:` prefix), for example `bte:stateOfHealth`;
- twin *instances*, when registered, follow the BattINFO registry resource pattern `https://w3id.org/battinfo/twin/{id}`;
- a hosted context is planned at `https://w3id.org/battinfo/twin/context`, mirroring the existing BattINFO context convention, so envelopes can reference the context by URL instead of inlining it.

!!! warning "Term IRIs are provisional"
    The `/twin` redirect rules are not yet part of the battinfo w3id registration, so the term IRIs do not dereference yet. Treat them as provisional until the redirects land. Deeper EMMO alignment (quantities, units) is planned for BTE 0.2 in coordination with BattINFO.

## SHACL over the RDF rendering

With the `battwin[shacl]` extra installed, the packaged SHACL shapes validate the JSON-LD rendering as RDF, catching problems that only exist at that layer (for example, non-canonical datetime literals). See the [validation guide](validation.md) for how the layers fit together.
