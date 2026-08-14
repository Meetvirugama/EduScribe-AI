import os
import sys
import asyncio
from dotenv import load_dotenv

os.environ["LITELLM_LOG"] = "ERROR"
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm.llm_manager import LLMManager
from services.llm.embedding_manager import EmbeddingManager
from services.llm.model_selector import TaskType

async def run():
    print("--- Testing LLM Pipeline ---")
    llm = LLMManager()
    
    # 1. Test standard generate
    try:
        messages = [{"role": "user", "content": "What is 2+2? Answer in 1 sentence."}]
        res = await llm.generate(
            task=TaskType.TRANSCRIPT_CLEANING, 
            messages=messages, 
            override_model="groq/llama-3.1-8b-instant"
        )
        print(f"Generate Success: {res.text}")
        
        # Test Cache
        res_cached = await llm.generate(
            task=TaskType.TRANSCRIPT_CLEANING, 
            messages=messages, 
            override_model="groq/llama-3.1-8b-instant"
        )
        print(f"Cache Hit Success: {res_cached.text}")
    except Exception as e:
        print(f"Generate Failed: {e}")


    # 3. Test Embedding Pipeline
    print("\n--- Testing Embedding Pipeline ---")
    emb = EmbeddingManager()
    try:
        res = await emb.embed("This is a test document.")
        tokens = res['usage']['total_tokens']
        print(f"Embedding Success: {tokens} tokens used.")
    except Exception as e:
        print(f"Embedding Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run())
