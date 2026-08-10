# Scaffold a twin from a BattINFO record

If the cell you are twinning has a record in the BattINFO registry, seed the envelope from its IRI instead of typing the identity by hand. The envelope *references* the record; it does not duplicate it.

## From the command line

```bash
battwin init --from-battinfo https://w3id.org/battinfo/spec/<id> -o cell.twin.json
```

## From Python

```python
from battwin import envelope_from_battinfo

env = envelope_from_battinfo("https://w3id.org/battinfo/spec/<id>")
```

Use `fetch_battinfo_record(iri)` if you just want the dereferenced JSON record.

## What gets mapped

The helper dereferences the IRI (following redirects, standard library only) and seeds the envelope:

- `identity`: the record's product name becomes `label`, along with manufacturer, model, and serial number where present;
- `specification.battinfo_record` carries the IRI itself, so the link back to the registry is explicit;
- `specification` convenience fields (chemistry, form factor, nominal capacity, nominal voltage) are filled where the record provides them.

Two behaviors worth knowing:

- the registry's `"unknown"` placeholder values become *absent* fields rather than the literal string `"unknown"`;
- `--label` and `--chemistry` (or the corresponding keyword arguments) override what the record says, useful when a record is sparse or when you want a bench-specific label.

If the record supplies no label and you pass none, initialization fails with a clear error, because `identity.label` is required.
