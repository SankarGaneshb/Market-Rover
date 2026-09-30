"""Lightweight stubs for all chromadb embedding functions."""
from typing import Any

class GenericEmbeddingFunction:
    def __init__(self, *args: Any, **kwargs: Any):
        pass
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return []

AmazonBedrockEmbeddingFunction = GenericEmbeddingFunction
CohereEmbeddingFunction = GenericEmbeddingFunction
HuggingFaceEmbeddingFunction = GenericEmbeddingFunction
InstructorEmbeddingFunction = GenericEmbeddingFunction
JinaEmbeddingFunction = GenericEmbeddingFunction
OllamaEmbeddingFunction = GenericEmbeddingFunction
OpenCLIPEmbeddingFunction = GenericEmbeddingFunction
RoboflowEmbeddingFunction = GenericEmbeddingFunction
SentenceTransformerEmbeddingFunction = GenericEmbeddingFunction
Text2VecEmbeddingFunction = GenericEmbeddingFunction
