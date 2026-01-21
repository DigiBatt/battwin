from __future__ import annotations

from typing import Any

from .ingestion import BdfDataset


def validate_bdf_dataset(dataset: BdfDataset) -> list[str]:
    """Perform lightweight validation checks on a BDF dataset."""
    issues: list[str] = []
    if dataset.payload is None:
        issues.append("BDF payload is empty.")
    if not dataset.metadata:
        issues.append("BDF metadata is missing or empty.")
    return issues


def validate_payload(payload: Any) -> list[str]:
    """Fallback validation for non-BDF payloads."""
    if payload is None:
        return ["Payload is empty."]
    return []
