# Working on battwin

This is a guide for anyone picking up battwin to keep building or testing it.
It explains how to set up, how the code is put together, the ideas behind the
format, and what is left to do.

## What battwin is

battwin defines the **Battery Twin Envelope**, or BTE: a way to describe a
battery digital twin as a single, shareable document. A twin, seen as data, is
just a bundle — an identity, a specification, one or more models, its current
state, and links to its data. battwin writes that bundle down as a small JSON
file and checks that it is well formed. It does not run simulations or host
twins; it only says what a twin *is* as a document, so different tools can
exchange them.

Two version numbers live here, and they are not the same thing: the **package**
version (what you `pip install`) and the **format** version (the BTE spec, in
`SPEC.md`). A new package release does not mean a new format.

## Getting set up

You need Python 3.10 or newer. On Windows, make the environment with `py -3`.

```
py -3 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,shacl]"
```

The package needs only `pydantic` and `jsonschema`. The `shacl` extra adds a
third, optional layer of checking.

## Running the checks

Every change should pass these before it is committed:

```
ruff check .
ruff format --check .
mypy src
pytest -q          # the test suite (currently 94 tests)
```

And, importantly for this package, a release-time check that the built package
actually contains its data files. battwin ships a JSON schema, a JSON-LD
context, and a set of SHACL shapes; if those are left out of the build, the
tool installs but cannot validate anything. So at release time: build the
package, install the built file into a fresh empty environment, and confirm it
can validate the example and load all three data files. This package has been
bitten twice by exactly this, so treat it as a required step, not a nicety.

## How the code is organized

Everything lives under `src/battwin/`, plus the spec:

- `SPEC.md` (at the repo root) — the written specification. This is the real
  product; the code is the reference version of it.
- `envelope.py` — the document itself, as Python objects, plus how it turns
  into JSON, how it is hashed, and how a new version links to the last one.
- `validate.py` — three ways to check a document: against the JSON schema,
  against the model rules, and (optionally) against the SHACL shapes.
- `schemas/`, `context/`, `shapes/` — the three data files that ship with the
  package. These are what non-Python tools use to check documents too.
- `cli.py` and `__main__.py` — the command-line tool.

## The ideas that hold the format together

- **Reference, don't copy.** An envelope points at BattINFO records, BPX
  parameter files, and BDF datasets by their address; it does not paste their
  contents in. It composes other standards rather than replacing them.
- **BattINFO owns the names.** All the linked-data terms live under the
  BattINFO web address. battwin does not invent its own namespace.
- **Documents are frozen.** Once made, an envelope does not change. Updating a
  twin means writing a new version whose fingerprint points back at the old
  one, so you can always check the chain.
- **Everyone should agree.** The three checking layers must not disagree about
  the same document, and the published schema is meant to be usable by tools
  that are not written in Python — so it has to be strict on its own.

## How we test new work

The same pattern that built this package works well here: write the change,
then have someone independent try hard to break it with real scripts before it
is accepted. For a format meant to be shared and hashed, the sharp edges are
always at the boundaries — dates that can be written two ways, empty values,
keys that one checker accepts and another rejects. That is where the review
effort pays off. Because the format has no outside users yet, this is the
cheap moment to get those details right.

## What is built and what is next

Built: the BTE 0.1.1 format and its written spec; the Python SDK; all three
checking layers; and the command-line tool including commands to print the
schema and context for other tools to use.

Next:

- Register the web addresses so the linked-data terms actually resolve (one
  change to the shared `w3id.org` redirect rules).
- BTE 0.2, lining the format's quantity terms up with the EMMO battery
  vocabulary, worked out together with BattINFO.
- Let a registry store and serve twins, and add `push`/`pull` commands so
  battwin can talk to it.
- A small helper to start an envelope from a battfeed data file's sidecar, so
  the two tools connect with less hand-copying.

## Known rough edges

None that lose or corrupt data. The main open item is that the linked-data web
addresses do not resolve yet (see "what is next"), so treat the term addresses
as provisional until the redirect rules are added.

## Releasing

Bump the **package** version in `pyproject.toml` (leave the BTE format version
alone unless the format itself changed), move the `[Unreleased]` notes under
the new version in `CHANGELOG.md`, build, run the data-files check above, and
upload. Delete old build files first.
