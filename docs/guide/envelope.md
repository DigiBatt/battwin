# The twin envelope

A Battery Twin Envelope is one JSON object, conventionally saved with the `.twin.json` suffix (suggested media type: `application/battery-twin+json`). This page walks through each section informally; the [specification](../spec.md) is the normative definition.

## The shape at a glance

```jsonc
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

## `id`: the twin, not the document

The `id` names the *twin* and stays identical across every version of it. Individual documents are distinguished by their `version` record and content hash. Any URN or IRI works; `new_envelope` generates a `urn:bte:` URN when you do not supply one.

## `identity`: what the twin mirrors

The one required field is `label`, a human-readable name. Optional fields identify the physical battery precisely: `manufacturer`, `model`, `serial_number`, `battinfo_iri` (the IRI of a BattINFO cell or cell-instance record), and `passport_id` (an EU Digital Product Passport identifier).

## `specification`: the design-level description

Prefer pointing at a BattINFO record via `battinfo_record` over duplicating fields. For standalone use there are convenience fields: `chemistry`, `form_factor`, `nominal_capacity_ah`, `nominal_voltage_volt`. Numeric field names carry unit suffixes following the BDF naming convention (`{quantity}_{unit}`, snake_case), which is why it is `nominal_capacity_ah` and not `nominalCapacity`.

## `models[]`: which models apply, and when they are valid

Each binding names a model the twin can be simulated with. `kind` is one of `bpx`, `battmo`, `pybamm`, or `custom`, and exactly one of `source` (a path or IRI) or `inline` (an embedded document, such as a BPX JSON object or an [ECM parameter set](ecm-sim.md)) must be present. An optional `validity` window declares the operating range the model is trusted in:

```json
{
  "kind": "custom",
  "name": "ocv-bezier-fit",
  "inline": { "curve": "bezier", "control_points": [[0.0, 3.35], [1.0, 2.0]] },
  "validity": {
    "temperature_celsius": [10.0, 40.0],
    "state_of_charge": [0.05, 1.0]
  }
}
```

Envelopes describe *which* models apply and *when they are valid*, never how to execute them.

## `state` and `state_history[]`: the estimated condition

A state snapshot records what was known about the battery at a moment in time: `as_of` (required), then optionally `state_of_charge` (0–1), `state_of_health` (0–1.5), `cycle_count`, `internal_resistance_ohm`, `energy_throughput_kwh`, `equivalent_full_cycles`, the estimation `method`, and `source_data` (the URI of the dataset the estimate derives from). When a new snapshot replaces `state`, the old one should be appended to `state_history` (oldest first), so the envelope carries its own trajectory.

## `data[]`: links to measurements

Each link has a `kind` (`bdf`, `feed`, or `other`), a `uri`, and optionally a `role` (such as `cycling`, `field`, `characterization`) and `description`. `bdf` links should point at conforming [BDF](https://github.com/battery-data-alliance/battery-data-format) datasets. The envelope links data; it never embeds it.

## `provenance`: who made this document

`created` (required), plus optional `created_by`, `tool`, and `funding`.

## `extensions`: namespaced facts that are not (yet) canonical

Vendor- or tool-specific facts live under namespaced keys of the form `<prefix>:<name>`, for example `"lab:fixture_id": "bench-07"`. The prefixes `bte:`, `schema:`, and `battinfo:` are reserved. Values may be any JSON except `null`, and extensions participate in canonical serialization and content hashing exactly like every other field. Consumers must ignore extension entries they do not understand. The exact key grammar is in [SPEC §3.8](../spec.md#38-extensions).

## `version`: the chain record

`number`, `previous` (the content hash of the predecessor document, absent only for version 1), `changed` (the top-level sections that differ from the predecessor), and `timestamp`. How the chain works, and how to verify it, is the subject of the [versioning guide](versioning.md).

## A complete example

A full worked envelope, a CR2032 cell with a BattINFO spec reference, an inline model stub, a state snapshot, a BDF data link, and an extensions block, lives at [`examples/cr2032.twin.json`](https://github.com/DigiBatt/battwin/blob/main/examples/cr2032.twin.json).
