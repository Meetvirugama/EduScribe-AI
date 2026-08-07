import logging
import json
from typing import Dict, Any, List

from services.llm.llm_manager import LLMManager
from services.llm.model_selector import TaskType
from services.llm.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class ContentIntelligenceService:
    def __init__(self):
        self.llm_manager = LLMManager()

    def _format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS."""
        if seconds is None:
            return "00:00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _get_transcript_text(self, transcript_segments: List[Dict]) -> str:
        """Join transcript segments into a plain text string."""
        return " ".join([seg.get("text", "") for seg in transcript_segments])

    def _get_timed_transcript(self, transcript_segments: List[Dict]) -> str:
        """Join transcript with timestamps."""
        lines = []
        for seg in transcript_segments:
            start_fmt = self._format_time(seg.get("start", 0))
            lines.append(f"[{start_fmt}] {seg.get('text', '')}")
        return "\n".join(lines)

    # ── Phase 1 / Core: Topics, Notes & Visual Integration ─────────────────

    async def generate_topics_and_notes(self, transcript_segments: List[Dict], frames: List[Dict]) -> Dict[str, Any]:
        """
        Generates a comprehensive summary, topics, and detailed markdown notes.
        Embeds frame images where relevant. (Phase 1–3 combined core pipeline)
        """
        logger.info("Generating topics and detailed notes...")
        
        # 1. Prepare Transcript
        transcript_text = self._get_timed_transcript(transcript_segments)

        # 2. Prepare Keyframes Metadata
        frames_meta = []
        for f in frames:
            time_fmt = self._format_time(f["time_sec"])
            # Format path for markdown embedding
            web_path = f["path"].replace("../storage", "/storage")
            ocr_text = f["ocr"] or "No text detected"
            frames_meta.append(f"- Time: {time_fmt}, Path: {web_path}, OCR: {ocr_text}")
        
        frames_context = "\n".join(frames_meta)

        prompt = f"""
        You are an expert AI tutor. Analyze the following video transcript and key visual frames.
        
        Your task is to generate a comprehensive set of educational notes.
        You must output ONLY valid JSON matching this exact structure:
        {{
            "summary": "A 2-3 paragraph high-level summary of the entire video.",
            "topics": [
                {{
                    "title": "Topic Name",
                    "start_time": "HH:MM:SS",
                    "end_time": "HH:MM:SS",
                    "notes_markdown": "Detailed markdown notes explaining this topic. Use bolding, bullet points, and code blocks if applicable. IMPORTANT: If any of the provided Keyframes are relevant to this topic, embed them in your markdown using the format: ![Visual Reference](Path)",
                    "key_takeaways": ["Takeaway 1", "Takeaway 2"]
                }}
            ]
        }}
        
        Available Keyframes:
        {frames_context}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse topics JSON: {e}")
            logger.debug(f"Raw output: {response['content']}")
            return {"summary": "Failed to generate notes.", "topics": []}

    # ── Phase 2: Content Understanding ──────────────────────────────────────

    async def extract_concepts_and_keywords(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Extracts key academic concepts, technical terms, and important keywords
        from the lecture transcript. (T13: Concept Extraction, T14: Keyword Extraction)
        """
        logger.info("Extracting concepts and keywords...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Analyze the following lecture transcript.
        Extract the most important academic concepts, technical terms, and keywords.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "concepts": [
                {{
                    "name": "Concept name",
                    "category": "Category (e.g. Algorithm, Data Structure, Theorem, Pattern)",
                    "importance": "high/medium/low",
                    "brief_description": "One-sentence description"
                }}
            ],
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "key_phrases": ["important phrase 1", "important phrase 2"]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse concepts/keywords JSON: {e}")
            return {"concepts": [], "keywords": [], "key_phrases": []}

    async def detect_learning_objectives(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Identifies what a learner will know/be able to do after watching the video.
        (T15: Learning Objective Detection)
        """
        logger.info("Detecting learning objectives...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert instructional designer. Analyze the following lecture transcript.
        Identify the learning objectives — what a student will know, understand, or be able to do
        after completing this lecture.
        
        Use Bloom's Taxonomy verbs (remember, understand, apply, analyze, evaluate, create).
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "learning_objectives": [
                {{
                    "objective": "Students will be able to...",
                    "bloom_level": "remember/understand/apply/analyze/evaluate/create",
                    "topic": "Related topic name"
                }}
            ],
            "target_audience": "Description of ideal audience",
            "estimated_study_time_minutes": 30
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert instructional designer that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.LEARNING_OBJECTIVE_DETECTION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse learning objectives JSON: {e}")
            return {"learning_objectives": [], "target_audience": "", "estimated_study_time_minutes": 0}

    async def detect_prerequisites_and_dependencies(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Detects prerequisite knowledge required to understand this lecture and
        dependencies between topics covered. (T16: Prerequisite Detection, T17: Dependency Detection)
        """
        logger.info("Detecting prerequisites and concept dependencies...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Analyze the following lecture transcript.
        Identify:
        1. Prerequisites — knowledge the student MUST have before watching this lecture
        2. Concept dependencies — which topics within the lecture depend on other topics

        You must output ONLY valid JSON matching this exact structure:
        {{
            "prerequisites": [
                {{
                    "topic": "Required prerequisite topic",
                    "importance": "essential/recommended/optional",
                    "reason": "Why this is needed"
                }}
            ],
            "concept_dependencies": [
                {{
                    "concept": "Concept A",
                    "depends_on": "Concept B",
                    "reason": "A requires understanding B first"
                }}
            ],
            "suggested_prior_courses": ["Course or topic name 1", "Course or topic name 2"]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.PREREQUISITE_DETECTION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse prerequisites JSON: {e}")
            return {"prerequisites": [], "concept_dependencies": [], "suggested_prior_courses": []}

    async def classify_difficulty(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Classifies the difficulty level and complexity of the lecture content.
        (T20: Difficulty Classification)
        """
        logger.info("Classifying content difficulty...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert educator. Analyze the following lecture transcript and classify its difficulty.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "overall_difficulty": 3,
            "difficulty_label": "Intermediate",
            "difficulty_breakdown": {{
                "conceptual_depth": 3,
                "mathematical_rigor": 2,
                "prerequisite_count": 4,
                "abstraction_level": 3
            }},
            "difficulty_justification": "Explanation of why this difficulty was assigned",
            "suitable_for": ["Advanced undergraduates", "Early graduate students"]
        }}
        
        Note: difficulty scale is 1 (Beginner) to 5 (Expert/Research Level).
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert educator that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.DIFFICULTY_CLASSIFICATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse difficulty JSON: {e}")
            return {"overall_difficulty": 3, "difficulty_label": "Intermediate", "difficulty_breakdown": {}, "difficulty_justification": "", "suitable_for": []}

    # ── Phase 3: Knowledge Enrichment ────────────────────────────────────────

    async def generate_definitions(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates clear, comprehensive definitions for all important terms
        and concepts found in the transcript. (T21: Definition Generation)
        """
        logger.info("Generating definitions...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, identify all important
        specialized terms, concepts, and jargon. Provide clear, comprehensive definitions
        suitable for a student learning this topic for the first time.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "definitions": [
                {{
                    "term": "Term or concept name",
                    "definition": "Clear, detailed definition",
                    "synonyms": ["alternative name 1", "alternative name 2"],
                    "related_terms": ["related concept 1", "related concept 2"],
                    "example_usage": "How this term is used in context"
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.DEFINITION_GENERATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse definitions JSON: {e}")
            return {"definitions": []}

    async def generate_step_by_step_explanations(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates step-by-step breakdowns of processes, algorithms, and procedures
        covered in the lecture. (T24: Step-by-Step Explanation)
        """
        logger.info("Generating step-by-step explanations...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, identify all processes,
        algorithms, procedures, or workflows that can be explained step-by-step.
        
        Provide detailed, numbered step-by-step breakdowns for each one.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "step_by_step_explanations": [
                {{
                    "process_name": "Name of the process or algorithm",
                    "overview": "Brief overview of what this process does",
                    "steps": [
                        {{
                            "step_number": 1,
                            "action": "What happens in this step",
                            "explanation": "Why this step is necessary",
                            "example": "Concrete example or illustration (if applicable)"
                        }}
                    ],
                    "common_pitfalls": ["Pitfall 1", "Pitfall 2"],
                    "time_complexity": "O(n) or similar (if applicable)",
                    "space_complexity": "O(1) or similar (if applicable)"
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.STEP_BY_STEP_EXPLANATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse step-by-step JSON: {e}")
            return {"step_by_step_explanations": []}

    async def generate_real_world_applications(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates real-world application examples, industry use cases, and practical
        tips for applying the concepts learned. (T31: Real-World Applications, T32: Industry Use Cases)
        """
        logger.info("Generating real-world applications and industry use cases...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor with broad industry knowledge. Based on the following transcript,
        identify the key concepts and generate compelling real-world applications and industry use cases.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "real_world_applications": [
                {{
                    "concept": "Concept name",
                    "application": "How this concept is applied in the real world",
                    "industries": ["Industry 1", "Industry 2"],
                    "specific_example": "A concrete real-world example with company/product name if possible",
                    "impact": "Why this application matters"
                }}
            ],
            "industry_use_cases": [
                {{
                    "industry": "Industry name",
                    "use_case": "How this industry uses the lecture concepts",
                    "tools_used": ["Tool or technology 1", "Tool or technology 2"]
                }}
            ],
            "career_relevance": ["Career path 1", "Career path 2"]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.REAL_WORLD_APPLICATIONS, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse real-world applications JSON: {e}")
            return {"real_world_applications": [], "industry_use_cases": [], "career_relevance": []}

    # ── Phase 4: Educational Enhancement ────────────────────────────────────

    async def generate_assessments(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates quizzes and flashcards based on the transcript.
        (T46: Quiz Generation, T47: Flashcard Generation)
        """
        logger.info("Generating assessments (Quiz & Flashcards)...")
        
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, generate a 5-question multiple choice quiz and 5 study flashcards.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "quiz": [
                {{
                    "question": "Question text?",
                    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
                    "correct_answer": "B) ...",
                    "explanation": "Why this is correct."
                }}
            ],
            "flashcards": [
                {{
                    "front": "Concept name",
                    "back": "Concept definition or explanation"
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.QUIZ_GENERATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse assessments JSON: {e}")
            return {"quiz": [], "flashcards": []}

    async def generate_examples(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates real-world analogies, numerical, and programming examples.
        (T36: Example Generation, T37: Numerical Examples, T38: Programming Examples)
        """
        logger.info("Generating educational examples...")
        
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, identify 3 key concepts.
        For each concept, generate a real-world analogy/example to help explain it.
        If applicable, also provide a mathematical/numerical example and a short programming/code example.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "examples": [
                {{
                    "concept": "Concept name",
                    "real_world_analogy": "A detailed real-world analogy...",
                    "numerical_example": "A math or numerical example (or null if not applicable)",
                    "programming_example": "A code snippet explaining it (or null if not applicable)"
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.EXAMPLE_GENERATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse examples JSON: {e}")
            return {"examples": []}

    async def detect_misconceptions_and_edge_cases(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Identifies conceptual misconceptions that students commonly have, edge cases
        to be aware of, and interview-perspective questions. 
        (T41: Misconception Detection, T43: Edge Case Detection, T44: Interview Perspective)
        """
        logger.info("Detecting misconceptions and edge cases...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor and educator. Based on the following transcript,
        identify potential misconceptions, edge cases, and generate interview-perspective insights.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "misconceptions": [
                {{
                    "misconception": "What students often incorrectly believe",
                    "correct_understanding": "The accurate explanation",
                    "why_it_happens": "Why students make this mistake"
                }}
            ],
            "edge_cases": [
                {{
                    "scenario": "Edge case or corner case description",
                    "what_happens": "Behavior or outcome in this edge case",
                    "how_to_handle": "Recommended approach"
                }}
            ],
            "interview_questions": [
                {{
                    "question": "Typical interview question on this topic",
                    "difficulty": "easy/medium/hard",
                    "key_points_to_cover": ["Point 1", "Point 2", "Point 3"]
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.MISCONCEPTION_DETECTION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse misconceptions/edge cases JSON: {e}")
            return {"misconceptions": [], "edge_cases": [], "interview_questions": []}

    async def generate_learning_support(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates common mistakes, misconceptions, best practices, and edge cases.
        (T40: Common Mistakes, T42: Best Practices)
        """
        logger.info("Generating learning support...")
        
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, generate advanced learning support.
        Identify common mistakes, potential misconceptions, best practices, and edge cases related to the concepts discussed.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "common_mistakes": ["Mistake 1...", "Mistake 2..."],
            "misconceptions": ["Misconception 1...", "Misconception 2..."],
            "best_practices": ["Best practice 1...", "Best practice 2..."],
            "edge_cases": ["Edge case 1...", "Edge case 2..."]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.COMMON_MISTAKES_DETECTION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse learning support JSON: {e}")
            return {
                "common_mistakes": [],
                "misconceptions": [],
                "best_practices": [],
                "edge_cases": []
            }

    # ── Phase 5: Assessment & Study Planning ─────────────────────────────────

    async def generate_learning_path(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates a personalized learning path recommendation based on the lecture content.
        (T53: Learning Path Recommendation)
        """
        logger.info("Generating learning path recommendations...")
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert educational advisor. Based on the following lecture transcript,
        generate a comprehensive learning path to master the topics covered.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "current_topic_summary": "Brief summary of what was covered",
            "learning_path": [
                {{
                    "step": 1,
                    "topic": "What to study next",
                    "reason": "Why this comes next",
                    "resources": ["Resource type 1", "Resource type 2"],
                    "estimated_hours": 5
                }}
            ],
            "mastery_milestones": [
                {{
                    "milestone": "Milestone description",
                    "how_to_verify": "How to know you've achieved it"
                }}
            ],
            "total_estimated_hours": 20,
            "recommended_practice": ["Practice activity 1", "Practice activity 2"]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert educational advisor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.LEARNING_PATH_RECOMMENDATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse learning path JSON: {e}")
            return {"current_topic_summary": "", "learning_path": [], "mastery_milestones": [], "total_estimated_hours": 0, "recommended_practice": []}

    # ── Phase 6 / Legacy: Glossary ────────────────────────────────────────────

    async def generate_glossary(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates a glossary of specialized terms and acronyms used in the video.
        """
        logger.info("Generating glossary...")
        
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, extract the top 10 most important specialized terms, jargon, or acronyms.
        Provide a concise, easy-to-understand definition for each.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "glossary": [
                {{
                    "term": "Term Name",
                    "definition": "Definition..."
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.DEFINITION_GENERATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse glossary JSON: {e}")
            return {"glossary": []}

    # ── Phase 7: Quality Assurance ────────────────────────────────────────────

    async def verify_facts(self, transcript_segments: List[Dict], topics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-references the generated topics and notes with the original transcript
        to identify hallucinations or factual inconsistencies.
        (T66: Fact Verification)
        """
        logger.info("Running Quality Assurance (Fact Verification)...")
        
        transcript_text = self._get_transcript_text(transcript_segments)
        generated_notes = json.dumps(topics_data, indent=2)

        prompt = f"""
        You are an expert Quality Assurance AI. Your job is to verify the factual consistency of the "Generated Notes" against the original "Transcript".
        If the Generated Notes contain claims, definitions, or statements that explicitly contradict or hallucinate beyond what is supported by the Transcript, flag them.
        Ignore stylistic differences or reasonable summarization. Only flag factual errors.
        
        You must output ONLY valid JSON matching this exact structure:
        {{
            "qa_warnings": [
                {{
                    "issue": "Brief description of the inconsistency",
                    "severity": "high/medium/low",
                    "correction": "How it should be corrected based on the transcript"
                }}
            ]
        }}
        
        Transcript:
        {transcript_text}
        
        Generated Notes:
        {generated_notes}
        """

        messages = [
            {"role": "system", "content": "You are a strict QA AI that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.FACT_VERIFICATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse QA JSON: {e}")
            return {"qa_warnings": []}

    # ── Phase 9 / Note Enrichment: Mind Map ──────────────────────────────────

    async def generate_mind_map(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Generates a Mermaid.js syntax mind map based on the transcript.
        (T48: Mind Map Generation)
        """
        logger.info("Generating Mermaid Mind Map...")
        
        transcript_text = self._get_transcript_text(transcript_segments)

        prompt = f"""
        You are an expert AI tutor. Based on the following transcript, create a hierarchical mind map of the core concepts.
        You must output ONLY valid JSON matching this exact structure containing the raw Mermaid.js code.
        Use standard mermaid flowchart syntax (graph TD or graph LR). Do NOT use complex unsupported diagram types. Keep it simple and beautiful.
        
        {{
            "mermaid_code": "graph TD\\n  A[Main Topic] --> B(Subtopic 1)\\n  A --> C(Subtopic 2)"
        }}
        
        Transcript:
        {transcript_text}
        """

        messages = [
            {"role": "system", "content": "You are an expert AI tutor that strictly outputs valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_manager.generate(TaskType.MIND_MAP_GENERATION, messages)
        
        try:
            parsed_json = ResponseParser.extract_json(response["content"])
            return parsed_json
        except Exception as e:
            logger.error(f"Failed to parse mind map JSON: {e}")
            return {"mermaid_code": ""}


content_intelligence = ContentIntelligenceService()
