import asyncio
import os
import sys

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm.llm_manager import LLMManager
from services.content.context import LectureContext
from schemas.content import LectureInput
from services.content.topic import TopicService
from services.content.detailed_notes import DetailedNotesGenerator

async def main():
    print("Initializing LLM Manager...")
    llm_manager = LLMManager()
    
    transcript_path = "storage/transcripts/pSVk-5WemQ0.txt"
    if not os.path.exists(transcript_path):
        print(f"Transcript not found at {transcript_path}")
        return
        
    print(f"Reading transcript from {transcript_path}...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()
    
    # We will use the first 5000 characters to keep the test fast and inexpensive
    # This represents roughly 5-10 minutes of talking
    truncated_transcript = transcript[:5000]
    print(f"Loaded {len(truncated_transcript)} characters for testing.")
    
    input_data = LectureInput(
        transcript=truncated_transcript,
        metadata={"title": "Generative AI Introduction (Hindi)"},
        segments=[],
        frames=[]
    )
    context = LectureContext(input=input_data)
    
    print("\n--- PHASE 2: Extracting Topics ---")
    topic_service = TopicService(llm_manager)
    await topic_service.extract_topics(context)
    
    print(f"Extracted {len(context.topics)} topics:")
    for t in context.topics:
        print(f" - {t.get('title')}")
    
    print("\n--- PHASE 3: Generating Detailed Notes ---")
    notes_generator = DetailedNotesGenerator(llm_manager)
    await notes_generator.generate_detailed_notes(context)
    
    print("\n\n=======================================================")
    print("                 FINAL RENDERED NOTES                  ")
    print("=======================================================")
    # Write to the file the user is currently viewing
    output_path = "/Users/meetvirugama/Desktop/EduScribe-AI/backend/full_test_outputs/pSVk-5WemQ0/step7_detailed_notes.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(context.state.detailed_notes_md)
        
    print(f"Notes successfully saved to {output_path}")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
