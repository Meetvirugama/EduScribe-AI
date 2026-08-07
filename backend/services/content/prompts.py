"""
services/content/prompts.py — Prompt Loading and Versioning

Combines Jinja2 markdown template loading with versioned prompt registration.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from string import Template
from typing import Any, Dict, List, Optional
from jinja2 import Template as JinjaTemplate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jinja2 File Loader
# ---------------------------------------------------------------------------

class PromptManager:
    """
    Loads and renders external markdown prompt templates using Jinja2.
    These are the static files in the backend/prompts/ directory.
    """
    PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../prompts"))
    
    @classmethod
    def render(cls, template_name: str, **kwargs) -> str:
        filepath = os.path.join(cls.PROMPTS_DIR, f"{template_name}.md")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt template {template_name}.md not found in {cls.PROMPTS_DIR}.")
            
        with open(filepath, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = JinjaTemplate(template_content)
        return template.render(**kwargs)

# ---------------------------------------------------------------------------
# Versioned Prompt Registry
# ---------------------------------------------------------------------------

_HISTORY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "prompts", "prompt_history.json"
)

@dataclass
class PromptVersion:
    """A single versioned prompt."""
    prompt_id: str           # e.g. "detailed_notes_v2"
    task: str                # TaskType value string
    version: int             # monotonically increasing
    template: str            # The prompt template with $variable placeholders
    description: str = ""   # Human-readable change notes
    created_at: str = ""     # ISO datetime
    is_active: bool = True

    def render(self, **kwargs: Any) -> str:
        """Render this prompt template with the given variables."""
        try:
            return Template(self.template).safe_substitute(**kwargs)
        except Exception as exc:
            logger.error("PromptVersion.render failed for %s: %s", self.prompt_id, exc)
            return self.template  # Return unrendered template on error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "task": self.task,
            "version": self.version,
            "description": self.description,
            "created_at": self.created_at,
            "is_active": self.is_active,
            # template is intentionally excluded from dict (potentially large)
        }

class PromptRegistry:
    """
    Central registry for all versioned prompts.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[PromptVersion]] = {}
        self._load_history()
        self._register_defaults()

    def register(
        self,
        task: str,
        template: str,
        *,
        description: str = "",
        force_activate: bool = True,
    ) -> PromptVersion:
        versions = self._store.setdefault(task, [])
        if force_activate:
            for v in versions:
                v.is_active = False

        new_version = len(versions) + 1
        pv = PromptVersion(
            prompt_id=f"{task}_v{new_version}",
            task=task,
            version=new_version,
            template=template,
            description=description,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
            is_active=force_activate,
        )
        versions.append(pv)
        self._save_history()
        logger.info("PromptRegistry: registered %s (version %d)", task, new_version)
        return pv

    def get(self, task: str) -> Optional[PromptVersion]:
        versions = self._store.get(task, [])
        for v in reversed(versions):
            if v.is_active:
                return v
        return versions[-1] if versions else None

    def get_by_id(self, prompt_id: str) -> Optional[PromptVersion]:
        for versions in self._store.values():
            for v in versions:
                if v.prompt_id == prompt_id:
                    return v
        return None

    def rollback(self, task: str, version: int) -> bool:
        versions = self._store.get(task, [])
        target = next((v for v in versions if v.version == version), None)
        if not target:
            logger.warning("PromptRegistry: version %d not found for task %s", version, task)
            return False

        for v in versions:
            v.is_active = False
        target.is_active = True
        self._save_history()
        logger.info("PromptRegistry: rolled back %s to version %d", task, version)
        return True

    def list_history(self, task: str) -> List[Dict[str, Any]]:
        return [v.to_dict() for v in self._store.get(task, [])]

    def all_tasks(self) -> List[str]:
        return list(self._store.keys())

    def _history_path(self) -> str:
        path = _HISTORY_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def _save_history(self) -> None:
        data: Dict[str, List[Dict]] = {}
        for task, versions in self._store.items():
            data[task] = [
                {**v.to_dict(), "template": v.template}
                for v in versions
            ]
        try:
            with open(self._history_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("PromptRegistry: could not save history: %s", exc)

    def _load_history(self) -> None:
        path = self._history_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for task, versions in data.items():
                self._store[task] = [
                    PromptVersion(
                        prompt_id=v["prompt_id"],
                        task=v["task"],
                        version=v["version"],
                        template=v.get("template", ""),
                        description=v.get("description", ""),
                        created_at=v.get("created_at", ""),
                        is_active=v.get("is_active", False),
                    )
                    for v in versions
                ]
            logger.info("PromptRegistry: loaded %d task prompts from history", len(self._store))
        except Exception as exc:
            logger.warning("PromptRegistry: could not load history: %s", exc)

    def _register_defaults(self) -> None:
        defaults = {
            "detailed_notes": (
                """You are an expert AI tutor. Analyze the following video transcript and key visual frames.

Your task is to generate a comprehensive set of educational notes.
You must output ONLY valid JSON matching this exact structure:
{
    "summary": "A 2-3 paragraph high-level summary of the entire video.",
    "topics": [
        {
            "title": "Topic Name",
            "start_time": "HH:MM:SS",
            "end_time": "HH:MM:SS",
            "notes_markdown": "Detailed markdown notes. Use bolding, bullet points, code blocks. Embed keyframes: ![Visual Reference](Path)",
            "key_takeaways": ["Takeaway 1", "Takeaway 2"],
            "citations": [{"timestamp": "HH:MM:SS", "source": "transcript"}]
        }
    ]
}

Available Keyframes:
$frames_context

Transcript:
$transcript_text""",
                "Initial detailed notes prompt with citation support",
            ),
            "concept_extraction": (
                """You are an expert AI tutor. Extract the most important academic concepts, technical terms, and keywords.

Output ONLY valid JSON:
{
    "concepts": [{"name": "...", "category": "...", "importance": "high|medium|low", "brief_description": "..."}],
    "keywords": ["keyword1", "keyword2"],
    "key_phrases": ["phrase 1", "phrase 2"]
}

Transcript:
$transcript_text""",
                "Initial concept extraction prompt",
            ),
        }

        for task, (template, desc) in defaults.items():
            if task not in self._store:
                self.register(task, template, description=desc)

prompt_registry = PromptRegistry()
