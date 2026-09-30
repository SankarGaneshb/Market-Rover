"""Lightweight chromadb.config stub."""

from typing import Any, Dict, Optional

class Settings:
    """Stub for chromadb.config.Settings."""
    def __init__(self, **kwargs: Any):
        self._data: Dict[str, Any] = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name, None)

    def __repr__(self) -> str:
        return f"Settings({self._data})"

class System:
    pass

class Component:
    pass

DEFAULT_DATABASE = "default_database"
DEFAULT_TENANT = "default_tenant"

__all__ = ["Settings", "System", "Component", "DEFAULT_DATABASE", "DEFAULT_TENANT"]
