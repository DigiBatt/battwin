# Namespaces and linked data

Every conforming envelope also renders as JSON-LD ([how to do it](../howto/jsonld.md)). This page explains the naming decisions behind that rendering.

## BattINFO owns the names

BTE deliberately introduces **no new namespace**. BattINFO (`https://w3id.org/battinfo`, a registered w3id namespace) is the authority for battery-related IRIs, and BTE terms live under it:

- vocabulary terms: `https://w3id.org/battinfo/twin#` (the `bte:` prefix), for example `bte:stateOfHealth`;
- twin *instances*, when registered, follow the BattINFO registry resource pattern `https://w3id.org/battinfo/twin/{id}`;
- a hosted context is planned at `https://w3id.org/battinfo/twin/context`, mirroring the existing BattINFO context convention, so envelopes can reference the context by URL instead of inlining it.

Why not a battwin namespace? Because a second battery vocabulary is exactly the fragmentation BTE exists to avoid. One authority for battery IRIs means one place to look a term up, and it keeps the format's identity separate from any one implementation's, in line with the [package-is-not-the-format principle](design.md#the-package-is-not-the-format).

The context maps identity fields to schema.org terms rather than minting equivalents, for the same reason.

```{admonition} Term IRIs are provisional
:class: warning

The `/twin` redirect rules are not yet part of the battinfo w3id registration, so the term IRIs do not dereference yet. Treat them as provisional until the redirects land. Deeper EMMO alignment (quantities, units) is planned for BTE 0.2 in coordination with BattINFO.
```

## Why a SHACL layer exists at all

Once an envelope is RDF, constraints can be stated and checked in RDF's own terms, and some things are naturally checked there (datatype-level datetime canonicality, for instance). The packaged SHACL shapes make that check portable to any RDF toolchain, not just battwin's. How the SHACL layer relates to the other two is covered in [how the validation layers fit together](validation.md).

## Where this connects to the rest of the stack

`identity.battinfo_iri` and `specification.battinfo_record` are ordinary fields in JSON, but in the JSON-LD rendering they become first-class links into the BattINFO knowledge graph, which is what lets a twin sit in a triple store next to the records it cites. The ECM Parameter Set format follows the same philosophy: its concepts are typed against the EMMO domain-equivalent-circuit-model ontology while the values stay in a plain JSON document.
