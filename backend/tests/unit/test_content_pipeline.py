import asyncio
import time
from services.llm.llm_manager import LLMManager
from services.content.pipeline import ContentPipeline

async def main():
    llm = LLMManager()
    pipeline = ContentPipeline(llm)
    
    transcript = "Welcome to Introduction to Computer Science. Today we're going to talk about recursion. Recursion is when a function calls itself. A base case is required to stop the recursion. For example, calculating factorial(5) means 5 * factorial(4), and so on until factorial(1) = 1. A common mistake is forgetting the base case, leading to infinite recursion."
    
    start_time = time.time()
    print("Starting pipeline...")
    result = await pipeline.generate_full_content(transcript)
    end_time = time.time()
    
    print(f"\nPipeline executed in {end_time - start_time:.2f} seconds.")
    print("\nConcepts:")
    print(result.get("concepts"))
    print("\nNotes Summary:")
    print(result.get("notes", {}).get("summary"))
    print("\nQuiz Questions generated:")
    print(len(result.get("quiz", {}).get("questions", [])))

if __name__ == "__main__":
    asyncio.run(main())
