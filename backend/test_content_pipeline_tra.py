import asyncio
import os
import json
import sys
from dataclasses import asdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm.llm_manager import LLMManager
from services.content.pipeline import ContentPipeline
from services.merge.models import MergedLecture, MergedSection

def ts_to_sec(ts):
    parts = ts.split(':')
    if len(parts) == 2:
        return int(parts[0])*60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    return 0.0

async def main():
    print("Initializing LLM Manager...")
    llm_manager = LLMManager()
    
    json_path = "storage/transcripts/tra.json"
    if not os.path.exists(json_path):
        print(f"Transcript JSON not found at {json_path}")
        return
        
    print(f"Reading transcript from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = []
    for entry in data:
        if not entry.get("timestamp"):
            continue
        start_sec = ts_to_sec(entry["timestamp"])
        text = entry["text"]
        if entry.get("heading"):
            text = f"[{entry['heading']}] {text}"
            
        segments.append({
            "start": start_sec,
            "text": text
        })
        
    # Calculate end times
    for i in range(len(segments) - 1):
        segments[i]["end"] = segments[i+1]["start"]
    # Truncate to avoid massive costs or LLM rate limits (Groq has strict limits)
    # 20 segments is a very small chunk to ensure it stays below the 6000 TPM limit
    test_segments = segments[:20]
    print(f"Using {len(test_segments)} segments for testing.")
        
    section = MergedSection(
        section_id="sec_1",
        start_time=test_segments[0]["start"] if test_segments else 0.0,
        end_time=test_segments[-1]["end"] if test_segments else 0.0,
        transcript_segments=test_segments,
        frames=[],
        scene_numbers=[]
    )
    
    merged_lecture = MergedLecture(
        video_id="tra_test",
        metadata={"title": "Machine Learning Introduction (Test)"},
        sections=[section],
        statistics={}
    )
    
    output_dir = os.path.join("full_test_outputs", "tra_test")
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting Content Pipeline ---")
    pipeline = ContentPipeline(llm_manager)
    context = await pipeline.build_learning_context(merged_lecture)
    
    print("\n--- Pipeline Complete, Saving Outputs ---")
    
    # Save Unified MD
    unified_md_path = os.path.join(output_dir, "step1_unified.md")
    with open(unified_md_path, "w", encoding="utf-8") as f:
        f.write(context.state.unified_md)
    print(f"Saved Unified MD to {unified_md_path}")
    
    # Save Detailed Notes MD
    detailed_notes_path = os.path.join(output_dir, "step3_detailed_notes.md")
    with open(detailed_notes_path, "w", encoding="utf-8") as f:
        f.write(context.state.detailed_notes_md)
    print(f"Saved Detailed Notes MD to {detailed_notes_path}")
    
    # Save State JSON
    state_json_path = os.path.join(output_dir, "learning_context_state.json")
    
    # Helper to serialize Pydantic models
    def pydantic_encoder(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
    with open(state_json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(context.state), f, indent=2, default=pydantic_encoder)
    print(f"Saved Full State JSON to {state_json_path}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
