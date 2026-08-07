"""
services/rag/structure_detector.py — Lecture Structure Detection

Identifies the logical organisation of a lecture from its transcript segments:
  - Chapter / section boundaries
  - Topic transitions
  - Introduction and conclusion segments
  - Recap / summary segments
  - Important announcements

The detected structure is used by TopicChunker and reported in the
generated notes as a table of contents.

Issue Resolved: #10 (no lecture structure detection), #9 (OCR+Transcript integration)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LectureSection:
    """A detected structural section of the lecture."""
    title: str
    section_type: str          # intro | main | recap | announcement | conclusion
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    start_time_str: str = "00:00:00"
    end_time_str: str = "00:00:00"
    summary: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "section_type": self.section_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start_time_str": self.start_time_str,
            "end_time_str": self.end_time_str,
            "summary": self.summary,
            "confidence": self.confidence,
        }


@dataclass
class LectureStructure:
    """Full detected structure for a lecture."""
    sections: List[LectureSection] = field(default_factory=list)
    title: str = ""
    subject: str = ""
    total_topics: int = 0
    has_introduction: bool = False
    has_conclusion: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "subject": self.subject,
            "total_topics": self.total_topics,
            "has_introduction": self.has_introduction,
            "has_conclusion": self.has_conclusion,
            "sections": [s.to_dict() for s in self.sections],
        }

    def as_topics(self) -> List[Dict[str, Any]]:
        """Convert sections into the topic list format expected by TopicChunker."""
        return [
            {
                "title": s.title,
                "start_time": s.start_time_str,
                "end_time": s.end_time_str,
            }
            for s in self.sections
            if s.section_type in ("main", "intro", "conclusion")
        ]


class LectureStructureDetector:
    """
    Detects the logical structure of a lecture using an LLM.

    Falls back gracefully to a single-section structure if the LLM call
    fails or the transcript is too short.
    """

    PROMPT_TEMPLATE = """You are an expert in educational content analysis.
Analyze the following lecture transcript and identify its logical structure.

Identify:
1. Introduction (overview, goals, agenda)
2. Main content sections / chapters (the core topics)
3. Recap / summary segments
4. Important announcements (assignments, deadlines, exam info)
5. Conclusion (closing remarks, next steps)

For each section provide:
- A clear, descriptive title
- The section type: one of: intro | main | recap | announcement | conclusion
- The approximate start and end timestamps (HH:MM:SS format)
- A one-sentence summary

Output ONLY valid JSON matching this exact structure:
{{
    "lecture_title": "Overall title of the lecture",
    "subject": "Subject area (e.g. Computer Science, Mathematics)",
    "sections": [
        {{
            "title": "Section title",
            "section_type": "intro|main|recap|announcement|conclusion",
            "start_time": "HH:MM:SS",
            "end_time": "HH:MM:SS",
            "summary": "One sentence summary",
            "confidence": 0.9
        }}
    ]
}}

Transcript (with timestamps):
{transcript}
"""

    def _format_transcript(self, segments: List[Dict[str, Any]], max_chars: int = 12000) -> str:
        """Format segments as timestamped text, truncated if too long."""
        lines: List[str] = []
        total = 0
        for seg in segments:
            start = seg.get("start", 0)
            m, s = divmod(int(start), 60)
            h, m = divmod(m, 60)
            line = f"[{h:02d}:{m:02d}:{s:02d}] {seg.get('text', '').strip()}"
            total += len(line)
            if total > max_chars:
                lines.append("[... transcript truncated for structure detection ...]")
                break
            lines.append(line)
        return "\n".join(lines)

    def _parse_time(self, ts: str) -> float:
        """Parse HH:MM:SS → seconds."""
        try:
            parts = ts.split(":")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except Exception:
            return 0.0

    def _fallback_structure(self, segments: List[Dict]) -> LectureStructure:
        """Return a single-section structure when detection fails."""
        end_time = segments[-1].get("end", segments[-1].get("start", 0)) if segments else 0
        m, s = divmod(int(end_time), 60)
        h, m = divmod(m, 60)
        return LectureStructure(
            title="Lecture",
            subject="Unknown",
            sections=[
                LectureSection(
                    title="Main Content",
                    section_type="main",
                    start_time=0.0,
                    end_time=end_time,
                    start_time_str="00:00:00",
                    end_time_str=f"{h:02d}:{m:02d}:{s:02d}",
                )
            ],
        )

    async def detect(
        self,
        transcript_segments: List[Dict[str, Any]],
        frames_data: Optional[List[Dict[str, Any]]] = None,
        llm_manager=None,
    ) -> LectureStructure:
        """
        Detect lecture structure using an LLM.

        If llm_manager is not provided, falls back to heuristic detection.
        """
        if not transcript_segments:
            return LectureStructure()

        if len(transcript_segments) < 10:
            logger.info("StructureDetector: transcript too short, using fallback structure.")
            return self._fallback_structure(transcript_segments)

        # Heuristic fallback if no LLM available
        if llm_manager is None:
            logger.info("StructureDetector: no LLM manager provided, using heuristic fallback.")
            return self._heuristic_detect(transcript_segments)

        transcript_text = self._format_transcript(transcript_segments)
        prompt = self.PROMPT_TEMPLATE.format(transcript=transcript_text)

        try:
            from services.llm.model_selector import TaskType
            messages = [
                {"role": "system", "content": "You are an expert educational content analyst. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ]
            response = await llm_manager.generate(TaskType.LECTURE_ANALYSIS, messages)

            # Parse response
            raw = getattr(response, "text", None) or str(response)
            if hasattr(response, "model_dump"):
                # It's a validated Pydantic object
                data = response.model_dump()
            else:
                import re as _re
                json_match = _re.search(r"\{.*\}", raw, _re.DOTALL)
                data = json.loads(json_match.group()) if json_match else {}

            sections = []
            for sec in data.get("sections", []):
                start_str = sec.get("start_time", "00:00:00")
                end_str = sec.get("end_time", "00:00:00")
                sections.append(LectureSection(
                    title=sec.get("title", "Unknown Section"),
                    section_type=sec.get("section_type", "main"),
                    start_time=self._parse_time(start_str),
                    end_time=self._parse_time(end_str),
                    start_time_str=start_str,
                    end_time_str=end_str,
                    summary=sec.get("summary", ""),
                    confidence=float(sec.get("confidence", 1.0)),
                ))

            structure = LectureStructure(
                title=data.get("lecture_title", ""),
                subject=data.get("subject", ""),
                total_topics=len([s for s in sections if s.section_type == "main"]),
                has_introduction=any(s.section_type == "intro" for s in sections),
                has_conclusion=any(s.section_type == "conclusion" for s in sections),
                sections=sections,
            )
            logger.info(
                "StructureDetector: found %d sections for lecture '%s'",
                len(sections), structure.title,
            )
            return structure

        except Exception as exc:
            logger.error("StructureDetector: LLM detection failed: %s — using heuristic fallback", exc)
            return self._heuristic_detect(transcript_segments)

    def _heuristic_detect(self, segments: List[Dict[str, Any]]) -> LectureStructure:
        """
        Keyword-based heuristic section detection.
        Looks for common lecture structure signals without an LLM call.
        """
        INTRO_KEYWORDS = {"welcome", "today", "agenda", "overview", "introduce", "start", "begin"}
        RECAP_KEYWORDS = {"recap", "summary", "conclude", "review", "wrap", "sum up", "in conclusion"}
        TRANSITION_KEYWORDS = {"next", "moving on", "let's look at", "now we'll", "the next topic"}

        sections: List[LectureSection] = []
        current_start = segments[0].get("start", 0.0) if segments else 0.0
        current_title = "Introduction"
        current_type = "intro"
        section_idx = 0

        def _make_ts(secs: float) -> str:
            m, s = divmod(int(secs), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        for i, seg in enumerate(segments):
            text = seg.get("text", "").lower()
            start = seg.get("start", 0.0)

            is_transition = any(kw in text for kw in TRANSITION_KEYWORDS)
            is_recap = any(kw in text for kw in RECAP_KEYWORDS)

            if is_recap and current_type != "recap":
                # Close current section
                sections.append(LectureSection(
                    title=current_title,
                    section_type=current_type,
                    start_time=current_start,
                    end_time=start,
                    start_time_str=_make_ts(current_start),
                    end_time_str=_make_ts(start),
                ))
                current_start = start
                current_title = "Summary & Recap"
                current_type = "recap"
                section_idx += 1

            elif is_transition and current_type == "main":
                sections.append(LectureSection(
                    title=current_title,
                    section_type="main",
                    start_time=current_start,
                    end_time=start,
                    start_time_str=_make_ts(current_start),
                    end_time_str=_make_ts(start),
                ))
                current_start = start
                current_title = f"Topic {section_idx + 1}"
                section_idx += 1

            elif section_idx == 0 and i > len(segments) * 0.1:
                # Transition out of intro
                sections.append(LectureSection(
                    title=current_title,
                    section_type="intro",
                    start_time=current_start,
                    end_time=start,
                    start_time_str=_make_ts(current_start),
                    end_time_str=_make_ts(start),
                ))
                current_start = start
                current_title = "Main Content"
                current_type = "main"
                section_idx += 1

        # Close last section
        if segments:
            end_time = segments[-1].get("end", segments[-1].get("start", 0))
            sections.append(LectureSection(
                title=current_title,
                section_type=current_type,
                start_time=current_start,
                end_time=end_time,
                start_time_str=_make_ts(current_start),
                end_time_str=_make_ts(end_time),
            ))

        return LectureStructure(
            title="Lecture",
            sections=sections,
            total_topics=len([s for s in sections if s.section_type == "main"]),
            has_introduction=any(s.section_type == "intro" for s in sections),
            has_conclusion=any(s.section_type == "conclusion" for s in sections),
        )


# Module-level singleton
structure_detector = LectureStructureDetector()
