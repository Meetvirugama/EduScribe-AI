"""
base_provider.py — Provider Exception Definitions

Defines the core transient and permanent exception types used for LLM provider 
resilience, retry, and fallback orchestration.

LLD Reference: §19 Retry Strategy
"""

class ProviderTransientError(Exception):
    """
    Raised for retryable, temporary provider failures.
    """

class ProviderPermanentError(Exception):
    """
    Raised for non-retryable, permanent provider failures.
    """

class ProviderCapabilityError(ProviderPermanentError):
    """400 Request/capability error (e.g. invalid request format for the model)."""
    pass

class ProviderAuthenticationError(ProviderPermanentError):
    """401/403 Invalid authentication or access permission."""
    pass

class ProviderModelNotFoundError(ProviderPermanentError):
    """404 Model unavailable (not found in the specific account/project)."""
    pass

class ProviderRateLimitError(ProviderTransientError):
    """429 Rate or quota limit reached."""
    pass

class ProviderServiceError(ProviderTransientError):
    """5xx Provider/gateway error or Timeout."""
    pass

class ModelOutputError(ProviderPermanentError):
    """
    Raised when the model's output cannot be parsed into JSON or fails schema validation.
    Inherits from ProviderPermanentError to bypass retries and fail fast to the next fallback tier.
    """
