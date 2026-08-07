import os
import json
import logging
import numpy as np
from typing import List, Dict, Any

from services.llm.llm_manager import LLMManager

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    A lightweight, numpy-based vector store that avoids heavy external dependencies.
    It chunks markdown text, generates embeddings via LiteLLM, and saves them to a local JSON.
    """
    def __init__(self):
        self.llm_manager = LLMManager()

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Simple paragraph-based chunking."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks

    async def build_index(self, video_id: str, markdown_content: str):
        """
        Chunks the markdown, generates embeddings, and saves to storage.
        """
        logger.info(f"Building vector index for video {video_id}...")
        
        storage_dir = os.path.join("storage", video_id)
        os.makedirs(storage_dir, exist_ok=True)
        embeddings_path = os.path.join(storage_dir, "embeddings.json")
        
        chunks = self._chunk_text(markdown_content)
        vector_data = []
        
        for i, chunk in enumerate(chunks):
            embedding = await self.llm_manager.generate_embeddings(chunk)
            if embedding:
                vector_data.append({
                    "id": f"chunk_{i}",
                    "text": chunk,
                    "embedding": embedding
                })
                
        with open(embeddings_path, "w", encoding="utf-8") as f:
            json.dump(vector_data, f, ensure_ascii=False)
            
        logger.info(f"Vector index built with {len(vector_data)} chunks.")

    async def search(self, video_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Searches the stored chunks for the query using cosine similarity.
        """
        embeddings_path = os.path.join("storage", video_id, "embeddings.json")
        if not os.path.exists(embeddings_path):
            logger.warning(f"No embeddings found for video {video_id}")
            return []
            
        with open(embeddings_path, "r", encoding="utf-8") as f:
            vector_data = json.load(f)
            
        query_embedding = await self.llm_manager.generate_embeddings(query)
        if not query_embedding:
            return []
            
        query_vec = np.array(query_embedding)
        
        results = []
        for item in vector_data:
            item_vec = np.array(item["embedding"])
            # Cosine similarity
            similarity = np.dot(query_vec, item_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(item_vec))
            results.append({
                "text": item["text"],
                "score": float(similarity)
            })
            
        # Sort by highest score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

vector_store = VectorStoreService()
