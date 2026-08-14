import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env variables for key manager
def load_env(filepath):
    if not os.path.exists(filepath):
        print(f"❌ .env not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_env(env_path)

import litellm
litellm.set_verbose = True

from services.llm.llm_manager import LLMManager
from services.llm.model_selector import TaskType

async def main():
    manager = LLMManager()

    print("==================================================")
    print("      Testing LLMManager Fallback Pipeline        ")
    print("==================================================")

    messages = [{"role": "user", "content": "What is Machine Learning? Answer in one sentence."}]

    print("\n1. Testing Tier 1 (Gemini)...")
    print("Routing request to Gemini fallback chain...")
    
    try:
        response = await manager.generate(
            task=TaskType.ROUTING, # Arbitrary task to get a model config
            messages=messages,
            override_model="gemini/gemma-4-26b-a4b-it" 
        )
        print("✅ SUCCESS! Gemini responded.")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ FAILED: {e}")


    print("\n2. Testing Tier 2 (Groq with WAF bypass)...")
    print("Routing request to Groq fallback chain...")
    try:
        response = await manager.generate(
            task=TaskType.ROUTING, 
            messages=messages,
            override_model="groq/openai/gpt-oss-120b"
        )
        print("✅ SUCCESS! Groq WAF bypass worked.")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
