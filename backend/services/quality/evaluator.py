import logging
import re
from dataclasses import dataclass
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    schema_valid: bool = True
    coverage_score: float = 0.0
    completeness_score: float = 0.0
    readability_score: float = 0.0
    hallucination_risk: float = 0.0
    overall_score: float = 0.0
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_valid": self.schema_valid,
            "coverage_score": round(self.coverage_score, 3),
            "completeness_score": round(self.completeness_score, 3),
            "readability_score": round(self.readability_score, 3),
            "hallucination_risk": round(self.hallucination_risk, 3),
            "overall_score": round(self.overall_score, 3),
            "warnings": self.warnings,
        }


class SchemaValidator:
    def validate(self, artifact_type: str, artifact_data: Any) -> bool:
        if not isinstance(artifact_data, dict):
            return False

        required_keys = {
            "quiz": ["quiz"],
            "flashcards": ["flashcards"],
            "mindmap": ["content"],
            "formula_sheet": ["formulas", "topic_groups"],
            "interview": ["technical_questions", "conceptual_questions"],
            "revision": ["quick_facts", "must_know_points"],
            "notes": ["summary", "topics"]
        }

        req_keys = required_keys.get(artifact_type, [])
        for key in req_keys:
            if key not in artifact_data:
                return False
        return True


class HallucinationGuard:
    @staticmethod
    def _extract_proper_nouns(text: str) -> set:
        words = re.findall(r"(?<![.!?]\s)(?<!\A)\b[A-Z][a-z]{2,}\b", text)
        return {w.lower() for w in words}

    def score(self, text: str, transcript_text: str,
              concepts: List[Any]) -> float:
        notes_proper = self._extract_proper_nouns(text)
        if not notes_proper:
            return 0.0

        transcript_lower = transcript_text.lower()
        concept_names = {getattr(c, "name", "").lower() for c in concepts}

        novel = {
            n for n in notes_proper if n not in transcript_lower and n not in concept_names}
        risk = len(novel) / len(notes_proper)
        return risk


class QualityEvaluator:
    def __init__(self) -> None:
        self._schema_validator = SchemaValidator()
        self._hallucination = HallucinationGuard()

    def evaluate_artifact(
        self,
        artifact_type: str,
        artifact_data: Any,
        transcript_text: str,
        concepts: List[Any] = None
    ) -> QualityReport:
        """Evaluate a single artifact."""
        schema_valid = self._schema_validator.validate(
            artifact_type, artifact_data)

        # Convert artifact to string for text-based checks
        artifact_text = str(artifact_data)

        hallucination_risk = self._hallucination.score(
            artifact_text, transcript_text, concepts or [])

        overall = 1.0 if schema_valid else 0.5
        overall -= (hallucination_risk * 0.5)

        warnings = []
        if not schema_valid:
            warnings.append(f"Invalid schema for {artifact_type}")
        if hallucination_risk > 0.3:
            warnings.append(
                f"Potential hallucination detected (risk: {hallucination_risk:.0%})")

        return QualityReport(
            schema_valid=schema_valid,
            hallucination_risk=hallucination_risk,
            overall_score=max(0.0, overall),
            warnings=warnings,
        )


quality_evaluator = QualityEvaluator()
