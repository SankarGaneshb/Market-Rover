"""Lightweight stub for chromadb google embedding function."""
from typing import Any

class GoogleGenerativeAiEmbeddingFunction:
    def __init__(self, *args: Any, **kwargs: Any):
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return []

GoogleGenerativeAIEmbeddingFunction = GoogleGenerativeAiEmbeddingFunction
GoogleEmbeddingFunction = GoogleGenerativeAiEmbeddingFunction
GoogleVertexEmbeddingFunction = GoogleGenerativeAiEmbeddingFunction

__all__ = [
    "GoogleGenerativeAiEmbeddingFunction",
    "GoogleGenerativeAIEmbeddingFunction",
    "GoogleEmbeddingFunction",
    "GoogleVertexEmbeddingFunction",
]
