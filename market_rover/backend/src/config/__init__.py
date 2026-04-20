"""Config package init."""
from src.config.database import get_pool, close_pool

__all__ = ["get_pool", "close_pool"]
