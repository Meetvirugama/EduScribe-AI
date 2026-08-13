import asyncio
import json
import os
import sys
import time
import logging

from services.llm.llm_manager import LLMManager
from services.content.pipeline import ContentPipeline
from services.merge.models import MergedLecture

# Reduce logging spam for the loop
logging.getLogger("httpx").setLevel(logging.WARNING)

async def main():
    print("Initializing LLM Manager...")
    llm_manager = LLMManager()
    pipeline = ContentPipeline(llm_manager)

    transcript_file = "storage/transcripts/tra.json"
    output_dir = "full_transcript_outputs"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Reading full transcript from {transcript_file}...")
    with open(transcript_file, "r") as f:
        raw_segments = json.load(f)

    # Convert to TranscriptSegment objects
    all_segments = []
    for i, seg in enumerate(raw_segments):
        start = seg.get("start", 0.0)
        dur = seg.get("duration", 0.0)
        end = start + dur
        all_segments.append(
            {
                "index": i,
                "start": start,
                "end": end,
                "text": seg.get("text", "")
            }
        )

    print(f"Total segments loaded: {len(all_segments)}")
    
    # Chunk the segments into groups of 20
    chunk_size = 20
    chunks = [all_segments[i:i + chunk_size] for i in range(0, len(all_segments), chunk_size)]
    print(f"Divided into {len(chunks)} chunks of size {chunk_size}.")

    all_detailed_notes = []

    for idx, chunk in enumerate(chunks):
        print(f"\n========================================")
        print(f"Processing Chunk {idx + 1}/{len(chunks)}...")
        print(f"========================================")
        
        # Build a temporary MergedLecture for this chunk
        chunk_text = " ".join([s.get("text", "") for s in chunk])
        from services.merge.models import MergedSection
        
        merged_section = MergedSection(
            section_id=f"chunk_{idx}",
            start_time=chunk[0].get("start", 0.0),
            end_time=chunk[-1].get("end", 0.0),
            transcript_segments=chunk,
            frames=[],
            scene_numbers=[]
        )

        merged_lecture = MergedLecture(
            video_id=f"chunk_{idx}",
            metadata={"title": f"Machine Learning Session - Part {idx+1}"},
            sections=[merged_section]
        )

        try:
            # Run the pipeline for the chunk
            context = await pipeline.build_learning_context(merged_lecture)
            
            # Save the chunk's notes
            chunk_notes = context.detailed_notes_md or ""
            all_detailed_notes.append(chunk_notes)
            
            # Save intermediate progress so we don't lose data if it crashes
            intermediate_file = os.path.join(output_dir, f"chunk_{idx+1}_notes.md")
            with open(intermediate_file, "w") as f:
                f.write(chunk_notes)
            
            print(f"Successfully processed chunk {idx + 1}. Notes size: {len(chunk_notes)}")
            
        except Exception as e:
            print(f"ERROR processing chunk {idx + 1}: {e}")
            # Add an error placeholder so we know it failed
            error_msg = f"\n> [!ERROR] Failed to process part {idx+1}: {e}\n"
            all_detailed_notes.append(error_msg)
            
            intermediate_file = os.path.join(output_dir, f"chunk_{idx+1}_notes.md")
            with open(intermediate_file, "w") as f:
                f.write(error_msg)

        if idx < len(chunks) - 1:
            # Pause slightly between chunks to help API rate limits recover naturally
            wait_time = 10
            print(f"Waiting {wait_time} seconds before next chunk to avoid rate limits...")
            time.sleep(wait_time)

    print("\n========================================")
    print("All chunks processed! Compiling final markdown...")
    print("========================================")

    final_markdown = "# Full Machine Learning Live Session Notes\n\n"
    for idx, notes in enumerate(all_detailed_notes):
        final_markdown += f"## Part {idx + 1}\n\n"
        final_markdown += notes
        final_markdown += "\n\n---\n\n"

    final_output_path = os.path.join(output_dir, "final_combined_notes.md")
    with open(final_output_path, "w") as f:
        f.write(final_markdown)

    print(f"Done! Full combined notes saved to {final_output_path}")

if __name__ == "__main__":
    asyncio.run(main())
