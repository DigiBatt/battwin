from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)


class BdfDependencyError(ImportError):
    """Raised when optional BDF dependencies are missing."""


class BdfIntegrationError(RuntimeError):
    """Raised when BDF payloads cannot be loaded with the installed API."""


class BdfConversionError(ValueError):
    """Raised when a BDF payload cannot be converted to a dataframe."""


@dataclass(frozen=True)
class BdfDataset:
    source: Path
    payload: Any
    metadata: Mapping[str, Any]

    def to_dataframe(self) -> "pd.DataFrame":
        try:
            import pandas as pd
        except ImportError as exc:
            raise BdfDependencyError(
                "pandas is required for dataframe conversion. "
                "Install with `pip install echoed[bdf]`."
            ) from exc

        if hasattr(self.payload, "to_dataframe"):
            return self.payload.to_dataframe()

        if isinstance(self.payload, dict):
            for key in ("data", "records", "measurements"):
                if key in self.payload:
                    return pd.DataFrame(self.payload[key])

        if isinstance(self.payload, list):
            return pd.DataFrame(self.payload)

        raise BdfConversionError("Unable to derive a dataframe from the BDF payload.")


def load_bdf(path: str | Path, metadata_only: bool = False) -> BdfDataset:
    """Load a BDF dataset using the optional `bdf` library."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"BDF source not found: {source}")

    bdf_module = _require_bdf()
    payload = _load_payload(bdf_module, source, metadata_only)
    metadata = _extract_metadata(payload)

    logger.info("Loaded BDF payload from %s", source)
    return BdfDataset(source=source, payload=payload, metadata=metadata)


def _require_bdf():
    try:
        import bdf  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BdfDependencyError(
            "bdf is required to load BDF datasets. Install with `pip install echoed[bdf]`."
        ) from exc
    return bdf


def _load_payload(bdf_module: Any, source: Path, metadata_only: bool) -> Any:
    for attr in ("load", "read", "open"):
        loader = getattr(bdf_module, attr, None)
        if loader is None:
            continue
        try:
            return loader(source, metadata_only=metadata_only)
        except TypeError:
            return loader(source)

    bdf_file = getattr(bdf_module, "BdfFile", None)
    if bdf_file is not None:
        return bdf_file(source)

    raise BdfIntegrationError("Unsupported bdf API; expected load/read/open or BdfFile.")


def _extract_metadata(payload: Any) -> Mapping[str, Any]:
    if payload is None:
        return {}

    if isinstance(payload, dict):
        return payload.get("metadata", payload.get("meta", {})) or {}

    metadata = getattr(payload, "metadata", None)
    if callable(metadata):
        return metadata() or {}
    if metadata is not None:
        return metadata

    meta = getattr(payload, "meta", None)
    if callable(meta):
        return meta() or {}
    if meta is not None:
        return meta

    return {}
