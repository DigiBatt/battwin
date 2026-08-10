# Anatomy of an envelope

A Battery Twin Envelope is one JSON object, conventionally saved with the `.twin.json` suffix (suggested media type: `application/battery-twin+json`). This page explains what each section is *for*; the [specification](../reference/specification.md) is the normative definition of each field.

## The shape at a glance

```javascript
{
  "bte_version": "0.1.1",
  "id": "urn:bte:energizer-cr2032:demo-001",
  "identity":      { "label": "...", "serial_number": "...", "battinfo_iri": "...", "passport_id": "..." },
  "specification": { "battinfo_record": "https://w3id.org/battinfo/cell-spec/...", "chemistry": "Li/MnO2" },
  "models":        [ { "kind": "bpx", "name": "...", "source": "params.bpx.json", "validity": { "...": "..." } } ],
  "state":         { "as_of": "2026-07-07T12:00:00Z", "state_of_charge": 0.82, "method": "coulomb_counting" },
  "data":          [ { "kind": "bdf", "uri": "data/SINTEF__DEMO-001__20260707_001.bdf.csv", "role": "cycling" } ],
  "provenance":    { "created": "...", "created_by": "...", "tool": "battwin/0.4.0" },
  "extensions":    { "lab:fixture_id": "bench-07" },
  "version":       { "number": 2, "previous": "sha256:...", "changed": ["state"], "timestamp": "..." }
}
```

Required at the top level: `bte_version`, `id`, `identity`, `provenance`, and `version`. Everything else may be omitted. Unknown top-level fields are invalid; vendor- or tool-specific facts go in `extensions`.

## `id` names the twin, not the document

The `id` stays identical across every version of the same twin; individual documents are distinguished by their `version` record and content hash. This split is what lets a registry say "the twin `urn:bte:...`" while an auditor says "the document with hash `sha256:...`", and both be precise.

## `identity` and `specification`: instance versus design

`identity` is what the twin mirrors, the *physical individual*: a label (the one required field), and optionally manufacturer, model, serial number, a `battinfo_iri` naming the cell's registry record, and a `passport_id` for EU Digital Product Passport linkage. `specification` is the *design-level* description of that kind of cell, and the preferred content is a single `battinfo_record` reference rather than duplicated fields. The convenience fields (`chemistry`, `form_factor`, `nominal_capacity_ah`, `nominal_voltage_volt`) exist for standalone use, and their names carry unit suffixes following the BDF naming convention (`{quantity}_{unit}`, snake_case), which is why it is `nominal_capacity_ah` and not `nominalCapacity`.

## `models[]` declares applicability, not execution

Each binding says *which* model applies (`kind`: `bpx`, `battmo`, `pybamm`, or `custom`; exactly one of `source` or `inline`) and *when it is valid*, via an optional `validity` operating window over temperature and state of charge. What a consumer does with that binding, and with which solver, is that consumer's business. A `solver_hint` field exists and is explicitly non-binding.

## `state` and `state_history[]` carry the trajectory

A snapshot records what was known at a moment: `as_of`, then optional estimates (`state_of_charge`, `state_of_health`, `cycle_count`, `internal_resistance_ohm`, lifetime `energy_throughput_kwh` and `equivalent_full_cycles`), plus `method` and `source_data` saying how the estimate was made and from which dataset. When a new snapshot replaces `state`, the old one is appended to `state_history`, so the envelope carries its own history rather than delegating it to whoever stores the files.

## `data[]` links measurements, never embeds them

Each link has a `kind` (`bdf`, `feed`, or `other`), a `uri`, and optionally a `role` and `description`. Time-series data is BDF's job; the envelope's job is to say which datasets belong to this twin and what role they play.

## `extensions` is the pressure valve

Real deployments always have facts the canonical schema does not cover yet. Rather than forcing forks, `extensions` accepts namespaced keys (`"lab:fixture_id": "bench-07"`) with reserved prefixes (`bte:`, `schema:`, `battinfo:`) kept out of bounds. Extensions hash and serialize exactly like every other field, and consumers must ignore entries they do not understand. The exact key grammar is [SPEC §3.8](../reference/specification.md#38-extensions).

## `provenance` and `version` make it citable

`provenance` says who created the document, with what tool, under what funding. `version` is the chain record: the number, the predecessor's content hash, the changed sections, and a timestamp. Together they let a document stand alone as a citable, checkable artifact.

## A complete example

A full worked envelope (a CR2032 cell with a BattINFO spec reference, an inline model stub, a state snapshot, a BDF data link, and an extensions block) lives at [`examples/cr2032.twin.json`](https://github.com/DigiBatt/battwin/blob/main/examples/cr2032.twin.json).
