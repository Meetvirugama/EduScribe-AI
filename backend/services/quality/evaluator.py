"""
services/quality/evaluator.py — Automatic Output Quality Evaluation

Scores AI-generated notes after pipeline completion:
  CoverageScorer     — Did the notes cover all detected topics?
  CompletenessScorer — Are all required sections present?
  ReadabilityScorer  — Flesch-Kincaid reading ease estimate
  HallucinationGuard — Are new proper nouns introduced that aren't in transcript?

Results are aggregated into a single overall_score (0.0–1.0).
Low-scoring outputs trigger a warning log but do not block the pipeline.

Issue Resolved: #8 (no automatic output quality evaluation)
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class QualityReport:
    coverage_score: float = 0.0       # 0–1: how many topics are covered
    completeness_score: float = 0.0   # 0–1: required sections present
    readability_score: float = 0.0    # 0–1: normalised Flesch-Kincaid
    hallucination_risk: float = 0.0   # 0–1: proportion of unknown proper nouns
    overall_score: float = 0.0        # weighted average
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coverage_score": round(self.coverage_score, 3),
            "completeness_score": round(self.completeness_score, 3),
            "readability_score": round(self.readability_score, 3),
            "hallucination_risk": round(self.hallucination_risk, 3),
            "overall_score": round(self.overall_score, 3),
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------

class CoverageScorer:
    """
    Checks whether each detected topic is mentioned in the generated notes.
    Score = proportion of detected topic titles found in the notes text.
    """

    def score(self, notes_text: str, topics_data: Dict[str, Any]) -> float:
        topics = topics_data.get("topics", [])
        if not topics:
            return 1.0  # no topics to check, not a failure

        notes_lower = notes_text.lower()
        covered = 0
        for topic in topics:
            title = topic.get("title", "").lower()
            if title and title in notes_lower:
                covered += 1

        return covered / len(topics)


class CompletenessScorer:
    """
    Validates that the required structural sections exist in the markdown.
    Score = proportion of required markers found.
    """

    REQUIRED_MARKERS = [
        "##",         # at least one heading
        "**",         # at least one bold term (key concept)
        "-",          # at least one bullet list
    ]

    PREFERRED_SECTIONS = [
        "summary",
        "topics",
        "key takeaway",
        "definition",
        "example",
    ]

    def score(self, notes_text: str) -> float:
        text_lower = notes_text.lower()

        # Required markers (weighted heavily)
        required_score = sum(
            1 for m in self.REQUIRED_MARKERS if m in notes_text
        ) / len(self.REQUIRED_MARKERS)

        # Preferred section keywords
        preferred_score = sum(
            1 for s in self.PREFERRED_SECTIONS if s in text_lower
        ) / len(self.PREFERRED_SECTIONS)

        # Minimum length check
        word_count = len(notes_text.split())
        length_score = min(1.0, word_count / 300)   # expect at least 300 words

        return (required_score * 0.4 + preferred_score * 0.4 + length_score * 0.2)


class ReadabilityScorer:
    """
    Estimates Flesch-Kincaid Reading Ease and normalises to 0–1.
    FK = 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    Higher FK = easier to read. Educational content targets 50–70.
    """

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip(".,!?;:")
        if len(word) <= 3:
            return 1
        vowels = "aeiouy"
        count = sum(1 for c in word if c in vowels)
        # Subtract silent 'e'
        if word.endswith("e"):
            count -= 1
        return max(1, count)

    def score(self, text: str) -> float:
        # Strip markdown
        clean = re.sub(r"[#*`\[\]()!>-]", " ", text)
        sentences = re.split(r"[.!?]+", clean)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = re.findall(r"\b[a-z]+\b", clean.lower())

        if not sentences or not words:
            return 0.5  # can't evaluate

        avg_sentence_len = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(w) for w in words) / len(words)
        fk = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables

        # Normalise: FK 0–100, target 50–70 for educational material
        # Map to 0–1: score peaks at FK=60, degrades outside 20–90
        return max(0.0, min(1.0, (fk - 20) / 70))


class HallucinationGuard:
    """
    Estimates hallucination risk by checking whether capitalised proper nouns
    in the generated notes exist in the original transcript.
    A high proportion of novel proper nouns is a hallucination signal.

    This is a heuristic — not a ground-truth detector. It flags unusual
    patterns for human review, not for automatic rejection.
    """

    @staticmethod
    def _extract_proper_nouns(text: str) -> set:
        # Words that start with uppercase (excluding first word of sentence)
        words = re.findall(r"(?<![.!?]\s)(?<!\A)\b[A-Z][a-z]{2,}\b", text)
        return {w.lower() for w in words}

    def score(self, notes_text: str, transcript_text: str) -> float:
        """Return hallucination risk (0 = no risk, 1 = high risk)."""
        notes_proper = self._extract_proper_nouns(notes_text)
        if not notes_proper:
            return 0.0

        transcript_lower = transcript_text.lower()
        novel = {n for n in notes_proper if n not in transcript_lower}
        risk = len(novel) / len(notes_proper)
        return risk


# ---------------------------------------------------------------------------
# Evaluator orchestrator
# ---------------------------------------------------------------------------

class QualityEvaluator:
    """
    Runs all scorers and produces a combined QualityReport.

    Weights:
      coverage     40%
      completeness 30%
      readability  20%
      hallucination 10% (inverse — lower risk = higher score)
    """

    def __init__(self) -> None:
        self._coverage = CoverageScorer()
        self._completeness = CompletenessScorer()
        self._readability = ReadabilityScorer()
        self._hallucination = HallucinationGuard()

    def evaluate(
        self,
        notes_text: str,
        transcript_segments: List[Dict[str, Any]],
        topics_data: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """
        Evaluate generated notes against the source transcript.

        Args:
            notes_text:          The final generated markdown string.
            transcript_segments: Raw Whisper segments (list of {text, start, end}).
            topics_data:         Output of generate_topics_and_notes (for coverage check).

        Returns:
            QualityReport with individual scores and overall score.
        """
        transcript_text = " ".join(
            seg.get("text", "") for seg in transcript_segments
        )

        coverage = self._coverage.score(notes_text, topics_data or {})
        completeness = self._completeness.score(notes_text)
        readability = self._readability.score(notes_text)
        hallucination_risk = self._hallucination.score(notes_text, transcript_text)

        overall = (
            coverage * 0.40
            + completeness * 0.30
            + readability * 0.20
            + (1.0 - hallucination_risk) * 0.10
        )

        warnings: List[str] = []
        if coverage < 0.5:
            warnings.append(f"Low topic coverage: {coverage:.0%} of topics mentioned in notes.")
        if completeness < 0.5:
            warnings.append("Notes appear incomplete: missing required sections.")
        if hallucination_risk > 0.3:
            warnings.append(
                f"Potential hallucination detected: {hallucination_risk:.0%} of proper nouns "
                f"in notes not found in transcript."
            )

        report = QualityReport(
            coverage_score=coverage,
            completeness_score=completeness,
            readability_score=readability,
            hallucination_risk=hallucination_risk,
            overall_score=overall,
            warnings=warnings,
        )

        log_fn = logger.warning if overall < 0.5 else logger.info
        log_fn(
            "QualityEvaluator: overall=%.2f coverage=%.2f completeness=%.2f "
            "readability=%.2f hallucination_risk=%.2f warnings=%d",
            overall, coverage, completeness, readability, hallucination_risk, len(warnings),
        )

        return report


# Module-level singleton
quality_evaluator = QualityEvaluator()
