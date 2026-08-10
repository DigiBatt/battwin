# CLI reference

Installing battwin puts a `battwin` command on your path; `python -m battwin` runs the identical interface. The CLI is small by design: validate, inspect, and scaffold documents. Anything that *runs* a twin (simulation, sync, hosting) is intentionally out of scope for the command line.

```console
$ battwin --version
battwin 0.4.0
```

## Commands

### `battwin validate`

```bash
battwin validate FILE [FILE ...] [--shacl]
```

Validates each file against the BTE spec (JSON Schema layer plus model rules) and prints one line per file, with the problems listed under any invalid one. `--shacl` also runs the packaged SHACL shapes over the JSON-LD rendering; it requires the `battwin[shacl]` extra and exits `2` with a clear message when the extra is missing.

```console
$ battwin validate cell.twin.json
ok       cell.twin.json
```

### `battwin init`

```bash
battwin init --label LABEL [options] -o FILE
battwin init --from-battinfo IRI [options] -o FILE
```

Scaffolds a minimal valid envelope. Options:

| Option | Meaning |
|---|---|
| `--label` | human-readable name of the twinned battery; required unless `--from-battinfo` supplies one, and overrides the record's name if both are given |
| `--from-battinfo IRI` | seed `identity` and `specification` from a BattINFO record IRI ([details](battinfo.md)); the envelope references the record, it does not copy it |
| `--chemistry` | convenience `specification.chemistry` value |
| `--id` | twin identifier (URN or IRI); generated if omitted |
| `--created-by` | `provenance.created_by` |
| `--jsonld` | write JSON-LD (with `@context`) instead of plain JSON |
| `-o, --out` | output path (required) |

### `battwin show`

```bash
battwin show FILE
```

Prints a human-readable summary of an envelope.

### `battwin hash`

```bash
battwin hash FILE
```

Prints the content hash (`sha256:...`) of an envelope in its canonical form. See [versioning and hashing](versioning.md).

### `battwin diff`

```bash
battwin diff A B
```

Compares two versions of a twin: reports the version numbers, the changed top-level sections, and whether the version chain is intact (`B.version.previous == hash(A)`).

### `battwin schema` and `battwin context`

```bash
battwin schema   > twin-envelope.schema.json
battwin context  > twin-envelope.context.jsonld
```

Print the packaged JSON Schema and JSON-LD context to stdout, so non-Python consumers can pull the language-neutral contracts without touching the SDK.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success; all files valid; version chain intact |
| `1` | at least one invalid file (`validate`), or different twins / broken chain (`diff`) |
| `2` | usage or environment error: missing file, unreadable or binary input, missing `--label`, or a missing optional extra (such as `--shacl` without `battwin[shacl]`) |
