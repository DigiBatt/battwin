# Verify a twin's version chain

Any consumer can check that a claimed successor document really derives from its predecessor, without trusting the party that produced it.

## From the command line

```console
$ battwin diff cell.twin.json cell.v2.twin.json
versions: 1 -> 2
changed sections: state
version chain: intact (b.previous == hash(a))
```

`diff` exits `0` when the chain is intact and `1` when the documents belong to different twins or the link is broken.

To get a single document's content hash:

```console
$ battwin hash cell.twin.json
sha256:3f7a...
```

## From Python

The check is one comparison:

```python
from battwin import load

a = load("cell.twin.json")
b = load("cell.v2.twin.json")
assert b.version.previous == a.content_hash()
```

For a longer history, walk the files pairwise; each document's `version.previous` must equal the content hash of the one before it.

## Without battwin

The hash is deliberately reproducible in any language: `"sha256:" + hex(sha256(canonical_json))`, where `canonical_json` serializes the document with sorted keys, `(",", ":")` separators, UTF-8, and null-valued fields omitted. The exact canonical form, including datetime normalization, is defined in [SPEC §4](../reference/specification.md#4-versioning-and-immutability).

## Related

- [Versioning and immutability](../explanation/versioning.md) explains why the format is built this way.
