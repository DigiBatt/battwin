# API reference

The public API is importable from the top-level `battwin` package; the modules below are where the objects live. Anything not documented here (names starting with `_`) is internal.

## `battwin.envelope`: the document model

```{eval-rst}
.. automodule:: battwin.envelope
   :no-members:

.. autodata:: battwin.envelope.BTE_VERSION

.. autopydantic_model:: battwin.envelope.TwinEnvelope
   :members:

.. autopydantic_model:: battwin.envelope.Identity
   :members:

.. autopydantic_model:: battwin.envelope.Specification
   :members:

.. autopydantic_model:: battwin.envelope.ModelBinding
   :members:

.. autopydantic_model:: battwin.envelope.ValidityWindow
   :members:

.. autopydantic_model:: battwin.envelope.StateSnapshot
   :members:

.. autopydantic_model:: battwin.envelope.DataLink
   :members:

.. autopydantic_model:: battwin.envelope.Provenance
   :members:

.. autopydantic_model:: battwin.envelope.VersionInfo
   :members:

.. autofunction:: battwin.envelope.new_envelope
```

## `battwin.io`: reading and writing

```{eval-rst}
.. automodule:: battwin.io
   :members:
```

## `battwin.validate`: validation

```{eval-rst}
.. automodule:: battwin.validate
   :members:
```

## `battwin.battinfo`: BattINFO helpers

```{eval-rst}
.. automodule:: battwin.battinfo
   :members:
```

## `battwin.ecm`: ECM parameter sets

```{eval-rst}
.. automodule:: battwin.ecm
   :members:
```

## `battwin.sim`: simulation (`battwin[sim]`)

```{eval-rst}
.. automodule:: battwin.sim
   :members:
```
