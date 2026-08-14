import logging
from typing import List

from .fallback_manager import FALLBACK_CHAIN
from .key_manager import KeyManager
from .model_selector import TaskType, get_model_config
from .validation import SchemaRegistry

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when the LLM configuration is invalid at startup."""

class StartupValidator:
    """Validates the entire LLM pipeline configuration at application startup."""

    @classmethod
    def validate(cls, key_manager: KeyManager = None) -> None:
        """Run all startup configuration checks."""
        logger.info("Validating LLM configuration...")
        km = key_manager or KeyManager()
        
        errors = []
        errors.extend(cls._validate_fallback_chain())
        errors.extend(cls._validate_keys(km))
        errors.extend(cls._validate_schemas())
        
        if errors:
            logger.error("LLM Configuration Invalid:")
            for err in errors:
                logger.error(f"  - {err}")
            raise ConfigurationError(f"LLM Configuration Invalid: {len(errors)} errors found.")
            
        logger.info("LLM configuration validated successfully.")

    @staticmethod
    def _validate_fallback_chain() -> List[str]:
        errors = []
        if not FALLBACK_CHAIN:
            errors.append("FALLBACK_CHAIN is empty. Check litellm_fallback_config.yaml.")
            
        tiers_present = set(model.tier for model in FALLBACK_CHAIN)
        if 1 not in tiers_present:
            errors.append("Fallback chain is missing Tier 1 (Primary) models.")
            
        return errors

    @staticmethod
    def _validate_keys(km: KeyManager) -> List[str]:
        errors = []
        providers_needed = set(model.provider for model in FALLBACK_CHAIN)
        
        for provider in providers_needed:
            if km.all_keys_exhausted(provider):
                # Using all_keys_exhausted as a quick check for 'are there any usable keys'
                errors.append(f"Fallback tier requires provider '{provider}', but no valid API keys were found.")
                
        return errors

    @staticmethod
    def _validate_schemas() -> List[str]:
        errors = []
        # Check that essential tasks are mapped correctly
        essential_tasks = [
            TaskType.CONCEPT_EXTRACTION,
            TaskType.EXAMPLE_EXTRACTION,
            TaskType.FORMULA_EXPLANATION,
            TaskType.KEY_POINTS_EXTRACTION,
            TaskType.RELATIONSHIP_EXTRACTION,
            TaskType.INTERVIEW_PERSPECTIVE
        ]
        
        for task in essential_tasks:
            schema = SchemaRegistry.get_schema(task)
            if schema.__name__ == "GenericTextOutput":
                errors.append(f"Task '{task.value}' is missing a specific Pydantic schema (falling back to GenericTextOutput).")
                
            try:
                # Ensure the task has a model config mapping
                get_model_config(task)
            except KeyError:
                errors.append(f"Task '{task.value}' does not have a routing configuration in model_selector.py.")
                
        return errors
