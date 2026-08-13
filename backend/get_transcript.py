from youtube_transcript_api import YouTubeTranscriptApi
import os

video_id = "pSVk-5WemQ0"
# Use Hindi transcript as the video doesn't have English
transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])

text = " ".join([t['text'] for t in transcript])

out_path = f"/Users/meetvirugama/Desktop/EduScribe-AI/backend/storage/transcripts/{video_id}.txt"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, "w") as f:
    f.write(text)

print(f"Saved transcript to {out_path}")
