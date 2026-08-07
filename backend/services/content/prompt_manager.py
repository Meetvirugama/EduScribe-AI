import os
from jinja2 import Template

class PromptManager:
    """
    Loads and renders external markdown prompt templates using Jinja2.
    """
    PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../prompts"))
    
    @classmethod
    def render(cls, template_name: str, **kwargs) -> str:
        filepath = os.path.join(cls.PROMPTS_DIR, f"{template_name}.md")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt template {template_name}.md not found in {cls.PROMPTS_DIR}.")
            
        with open(filepath, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = Template(template_content)
        return template.render(**kwargs)
