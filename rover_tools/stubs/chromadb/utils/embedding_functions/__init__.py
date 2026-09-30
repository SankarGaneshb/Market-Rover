"""Lightweight chromadb.utils.embedding_functions stub."""

from typing import Any

class EmbeddingFunction:
    def __init__(self, *args: Any, **kwargs: Any):
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return []

class DefaultEmbeddingFunction(EmbeddingFunction):
    pass

class OpenAIEmbeddingFunction(EmbeddingFunction):
    pass

class GoogleGenerativeAIEmbeddingFunction(EmbeddingFunction):
    pass

class ONNXMiniLM_L6_V2(EmbeddingFunction):
    pass

class AmazonBedrockEmbeddingFunction(EmbeddingFunction):
    pass

class CohereEmbeddingFunction(EmbeddingFunction):
    pass

class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    pass

class InstructorEmbeddingFunction(EmbeddingFunction):
    pass

class JinaEmbeddingFunction(EmbeddingFunction):
    pass

class OllamaEmbeddingFunction(EmbeddingFunction):
    pass

class OpenCLIPEmbeddingFunction(EmbeddingFunction):
    pass

class RoboflowEmbeddingFunction(EmbeddingFunction):
    pass

class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    pass

class Text2VecEmbeddingFunction(EmbeddingFunction):
    pass

__all__ = [
    "EmbeddingFunction",
    "DefaultEmbeddingFunction",
    "OpenAIEmbeddingFunction",
    "GoogleGenerativeAIEmbeddingFunction",
    "ONNXMiniLM_L6_V2",
    "AmazonBedrockEmbeddingFunction",
    "CohereEmbeddingFunction",
    "HuggingFaceEmbeddingFunction",
    "InstructorEmbeddingFunction",
    "JinaEmbeddingFunction",
    "OllamaEmbeddingFunction",
    "OpenCLIPEmbeddingFunction",
    "RoboflowEmbeddingFunction",
    "SentenceTransformerEmbeddingFunction",
    "Text2VecEmbeddingFunction",
]
