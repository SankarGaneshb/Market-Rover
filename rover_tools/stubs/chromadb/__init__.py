"""Lightweight pure-Python stub for chromadb providing configuration models and type signatures without heavy binary wheels."""

from typing import Any, Optional

__version__ = "0.6.0"

class Client:
    def __init__(self, *args: Any, **kwargs: Any):
        pass

class HttpClient(Client):
    pass

class PersistentClient(Client):
    pass

class EphemeralClient(Client):
    pass

def configure(**kwargs: Any) -> None:
    pass

__all__ = [
    "Client",
    "HttpClient",
    "PersistentClient",
    "EphemeralClient",
    "configure",
    "__version__",
]
