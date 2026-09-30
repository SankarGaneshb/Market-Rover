"""Lightweight chromadb.config stub."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

class Settings(BaseModel):
    """Stub for chromadb.config.Settings compatible with Pydantic v2 validation."""
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    persist_directory: Optional[str] = "./.chroma"
    allow_reset: Optional[bool] = True
    is_persistent: Optional[bool] = True

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.any_schema()

class System:
    pass

class Component:
    pass

DEFAULT_DATABASE = "default_database"
DEFAULT_TENANT = "default_tenant"

__all__ = ["Settings", "System", "Component", "DEFAULT_DATABASE", "DEFAULT_TENANT"]
