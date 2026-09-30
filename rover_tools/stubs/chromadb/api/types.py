"""Lightweight chromadb.api.types stub."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

L = TypeVar("L")
D = TypeVar("D")

URI = str
URIs = List[URI]
ID = str
IDs = List[ID]
Embedding = List[float]
Embeddings = List[Embedding]
Document = str
Documents = List[Document]
Image = Any
Images = List[Image]
Metadata = Dict[str, Any]
Metadatas = List[Metadata]
CollectionMetadata = Dict[str, Any]
UpdateCollectionMetadata = Dict[str, Any]
UpdateMetadata = Dict[str, Any]

Where = Dict[str, Any]
WhereDocument = Dict[str, Any]
QueryResult = Dict[str, Any]
GetResult = Dict[str, Any]
Include = List[str]
Loadable = Any

class DataLoader(Protocol[L]):
    def __call__(self, uris: URIs) -> L:
        ...

class EmbeddingFunction(Protocol[D]):
    def __call__(self, input: D) -> Embeddings:
        ...

class ChromaDBClientType:
    pass

class ChromaDBCollectionCreateParams:
    pass

class ChromaDBCollectionSearchParams:
    pass

__all__ = [
    "URI",
    "URIs",
    "ID",
    "IDs",
    "Embedding",
    "Embeddings",
    "Document",
    "Documents",
    "Image",
    "Images",
    "Metadata",
    "Metadatas",
    "CollectionMetadata",
    "UpdateCollectionMetadata",
    "UpdateMetadata",
    "Where",
    "WhereDocument",
    "QueryResult",
    "GetResult",
    "Include",
    "Loadable",
    "DataLoader",
    "EmbeddingFunction",
    "ChromaDBClientType",
    "ChromaDBCollectionCreateParams",
    "ChromaDBCollectionSearchParams",
]
