"""Lightweight stub for chromadb embedding function submodules."""
from typing import Any

class GoogleGenerativeAIEmbeddingFunction:
    def __init__(self, *args: Any, **kwargs: Any):
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return []

GoogleEmbeddingFunction = GoogleGenerativeAIEmbeddingFunction

__all__ = ["GoogleGenerativeAIEmbeddingFunction", "GoogleEmbeddingFunction"]
