# Validate envelope documents

## From the command line

```console
$ battwin validate cell.twin.json broken.twin.json
ok       cell.twin.json
INVALID  broken.twin.json
  - $.models[0]: exactly one of 'source' or 'inline' is required
```

`battwin validate` accepts multiple files, prints one line per file with the problems listed under any invalid one, and exits `1` if any file is invalid.

## Include the SHACL layer

Install the extra, then pass `--shacl`:

```bash
pip install "battwin[shacl]"
battwin validate --shacl cell.twin.json
```

This additionally checks the JSON-LD rendering against the packaged SHACL shapes. Without the extra installed, `--shacl` exits `2` with a message telling you what to install.

## From Python

```python
from battwin import validate_file, validate_dict

problems = validate_file("cell.twin.json")   # list[str], empty = valid
problems = validate_dict(doc)                # same, for a parsed dict
problems = validate_dict(doc, shacl=True)    # include the SHACL layer
```

Both functions return all problems from all requested layers rather than stopping at the first, so one pass tells you everything that is wrong.

## Validate an ECM Parameter Set

```python
from battwin.ecm import ecm_ps_problems, validate_ecm_ps_file

problems = validate_ecm_ps_file("cell.ecm-ps.json")  # list[str], empty = valid
problems = ecm_ps_problems(doc)                    # for a parsed dict
```

## Related

- [How the validation layers fit together](../explanation/validation.md) explains what each layer checks and why they must agree.
- [Use the contracts outside Python](contracts.md) covers validating with the packaged schema in other languages.
