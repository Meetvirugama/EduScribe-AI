import os
import json
from typing import Dict, Any
from .models import CanonicalTranscript
from core.config import settings

class ExporterService:
    """
    Exports a CanonicalTranscript to TXT, SRT, VTT, and JSON formats.
    """
    
    @staticmethod
    def export_all(transcript: CanonicalTranscript) -> Dict[str, str]:
        export_dir = os.path.join(settings.UPLOAD_DIR, "exports", transcript.video_id)
        os.makedirs(export_dir, exist_ok=True)
        
        paths = {}
        
        # 1. TXT Export
        txt_path = os.path.join(export_dir, f"{transcript.video_id}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript.full_text)
        paths["txt"] = txt_path
        
        # 2. Timestamped TXT
        ts_txt_path = os.path.join(export_dir, f"{transcript.video_id}_timestamped.txt")
        with open(ts_txt_path, "w", encoding="utf-8") as f:
            for seg in transcript.segments:
                # Format: [HH:MM:SS] Text
                hours, remainder = divmod(int(seg.start), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                f.write(f"{time_str} {seg.text}\n")
        paths["timestamped_txt"] = ts_txt_path
        
        # 3. SRT Export
        srt_path = os.path.join(export_dir, f"{transcript.video_id}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            for seg in transcript.segments:
                f.write(f"{seg.index + 1}\n")
                f.write(f"{ExporterService._format_time_srt(seg.start)} --> {ExporterService._format_time_srt(seg.end)}\n")
                f.write(f"{seg.text}\n\n")
        paths["srt"] = srt_path
        
        # 4. VTT Export
        vtt_path = os.path.join(export_dir, f"{transcript.video_id}.vtt")
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in transcript.segments:
                f.write(f"{ExporterService._format_time_vtt(seg.start)} --> {ExporterService._format_time_vtt(seg.end)}\n")
                f.write(f"{seg.text}\n\n")
        paths["vtt"] = vtt_path
        
        # 5. JSON Export
        json_path = os.path.join(export_dir, f"{transcript.video_id}.json")
        json_data = {
            "video_id": transcript.video_id,
            "language": transcript.language,
            "source_type": transcript.source_type,
            "segments": [
                {
                    "index": s.index,
                    "start": s.start,
                    "end": s.end,
                    "text": s.text
                } for s in transcript.segments
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        paths["json"] = json_path
        
        return paths

    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    def _format_time_vtt(seconds: float) -> str:
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
