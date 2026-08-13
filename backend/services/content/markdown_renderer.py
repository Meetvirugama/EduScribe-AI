"""
services/content/markdown_renderer.py

Deterministic Markdown renderer.
Converts structured LLM JSON outputs into consistent Markdown.
"""

from typing import Dict, Any, List

class MarkdownRenderer:
    """Renders structured topic notes into Markdown."""

    @staticmethod
    def render_topic(topic_data: Dict[str, Any]) -> str:
        """
        Renders a single topic note dictionary into a Markdown string.
        Gracefully skips empty or missing sections.
        """
        md = []
        
        title = topic_data.get("title", "Untitled Topic")
        md.append(f"## {title}")
        md.append("")

        if overview := topic_data.get("overview"):
            md.append("### Overview")
            md.append(overview)
            md.append("")

        if core_idea := topic_data.get("core_idea"):
            md.append("### Core Idea")
            md.append(core_idea)
            md.append("")

        if steps := topic_data.get("steps"):
            if isinstance(steps, list) and len(steps) > 0:
                md.append("### How It Works (Steps)")
                for i, step in enumerate(steps, 1):
                    md.append(f"{i}. {step}")
                md.append("")

        if terms := topic_data.get("important_terms"):
            if isinstance(terms, list) and len(terms) > 0:
                md.append("### Important Terms")
                md.append("| Term | Meaning |")
                md.append("|---|---|")
                for term_obj in terms:
                    term = term_obj.get("term", "")
                    meaning = term_obj.get("meaning", "")
                    md.append(f"| **{term}** | {meaning} |")
                md.append("")

        if formulas := topic_data.get("formulas"):
            if isinstance(formulas, list) and len(formulas) > 0:
                md.append("### Mathematical Formulation")
                for formula in formulas:
                    expr = formula.get("expression", "")
                    expl = formula.get("explanation", "")
                    md.append(f"**{expr}**")
                    if expl:
                        md.append(f"> {expl}")
                    md.append("")
                md.append("")

        if examples := topic_data.get("examples"):
            if isinstance(examples, list) and len(examples) > 0:
                md.append("### Examples")
                for ex in examples:
                    if isinstance(ex, str):
                        md.append(f"- {ex}")
                    elif isinstance(ex, dict):
                        prob = ex.get("problem", "")
                        sol = ex.get("solution", "")
                        md.append(f"**Scenario:** {prob}\n**Solution:** {sol}")
                        md.append("")
                md.append("")

        if relationships := topic_data.get("relationships"):
            if isinstance(relationships, list) and len(relationships) > 0:
                md.append("### Relationships With Other Concepts")
                for rel in relationships:
                    md.append(f"- {rel}")
                md.append("")

        if misconceptions := topic_data.get("misconceptions"):
            if isinstance(misconceptions, list) and len(misconceptions) > 0:
                md.append("### Common Misconceptions")
                for misc in misconceptions:
                    md.append(f"- {misc}")
                md.append("")

        if takeaways := topic_data.get("key_takeaways"):
            if isinstance(takeaways, list) and len(takeaways) > 0:
                md.append("### Key Takeaways / Exam Perspective")
                for pt in takeaways:
                    md.append(f"- {pt}")
                md.append("")

        return "\n".join(md)

    @staticmethod
    def compile_final_notes(lecture_title: str, topic_markdowns: List[str]) -> str:
        """Assembles the final comprehensive detailed notes."""
        md = []
        md.append(f"# {lecture_title}")
        md.append("")
        
        md.append("## Detailed Notes")
        md.append("")
        
        for t_md in topic_markdowns:
            md.append(t_md)
            md.append("---")
            md.append("")
            
        return "\n".join(md)
