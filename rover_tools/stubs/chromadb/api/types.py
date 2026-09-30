"""Lightweight chromadb.api.types stub."""

from typing import Any, Dict, List, Optional, Protocol, Union

Documents = List[str]
Embeddings = List[List[float]]
IDs = List[str]
Metadatas = List[Dict[str, Any]]
Where = Dict[str, Any]
WhereDocument = Dict[str, Any]
QueryResult = Dict[str, Any]
GetResult = Dict[str, Any]
Include = List[str]
DataLoader = Any

class EmbeddingFunction(Protocol):
    def __call__(self, input: Documents) -> Embeddings:
        ...

class ChromaDBClientType:
    pass

class ChromaDBCollectionCreateParams:
    pass

class ChromaDBCollectionSearchParams:
    pass

__all__ = [
    "Documents",
    "Embeddings",
    "IDs",
    "Metadatas",
    "Where",
    "WhereDocument",
    "QueryResult",
    "GetResult",
    "Include",
    "DataLoader",
    "EmbeddingFunction",
    "ChromaDBClientType",
    "ChromaDBCollectionCreateParams",
    "ChromaDBCollectionSearchParams",
]
