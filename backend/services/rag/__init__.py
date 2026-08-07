"""
services/rag/__init__.py

Public exports for the RAG (Retrieval-Augmented Generation) package.
"""
from .chunker import ChunkStrategy, ChunkerFactory, Chunk
from .embedding_store import EmbeddingStore, embedding_store
from .retriever import HybridRetriever, MMRRetriever, hybrid_retriever
from .context_optimizer import ContextOptimizer, context_optimizer
from .structure_detector import LectureStructureDetector, structure_detector
from .pipeline import VectorStoreService, vector_store

__all__ = [
    "ChunkStrategy",
    "ChunkerFactory",
    "Chunk",
    "EmbeddingStore",
    "embedding_store",
    "HybridRetriever",
    "MMRRetriever",
    "hybrid_retriever",
    "ContextOptimizer",
    "context_optimizer",
    "LectureStructureDetector",
    "structure_detector",
]
