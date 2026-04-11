"""Common utilities and helpers for workflow stages."""

from __future__ import annotations

from typing import Any


def _get_field(obj: Any, field: str) -> Any:
    """Polymorphically extract a field from a dataclass object or a dictionary.

    This helper is used across stage implementations to handle state entries that
    may be either structured objects (from internal logic) or raw dictionaries
    (from persistence or external tools).

    Args:
        obj: The object or dictionary to extract the field from.
        field: The name of the field to extract.

    Returns:
        The value of the field if found, otherwise None.
    """
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None
