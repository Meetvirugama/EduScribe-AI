import logging
import litellm
from .base_provider import (
    ProviderTransientError, ProviderPermanentError,
    ProviderCapabilityError, ProviderAuthenticationError,
    ProviderModelNotFoundError, ProviderRateLimitError,
    ProviderServiceError
)
from .pipeline import RequestContext
from .key_manager import KeyManager

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Translates raw LiteLLM exceptions into precise Provider resilience exceptions."""

    @staticmethod
    def handle_litellm_error(
            exc: Exception, provider: str, model: str, context: RequestContext,
            key_manager: KeyManager = None, api_key: str = None) -> None:
        err_msg = str(exc)
        req_id = context.request_id
        task_val = context.task.value

        if isinstance(exc, (ProviderTransientError, ProviderPermanentError)):
            raise exc

        if isinstance(exc, litellm.RateLimitError):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=RateLimitError (429)")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "rate_limit")
            raise ProviderRateLimitError(f"RateLimitError: {err_msg}") from exc

        elif isinstance(exc, litellm.AuthenticationError):
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=AuthenticationError (401/403)")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "auth")
            raise ProviderAuthenticationError(
                f"AuthenticationError: {err_msg}") from exc

        elif isinstance(exc, litellm.NotFoundError):
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=NotFoundError (404)")
            if key_manager and api_key:
                key_manager.mark_model_disabled(provider, api_key, model)
            raise ProviderModelNotFoundError(f"NotFoundError: {err_msg}") from exc

        elif isinstance(exc, litellm.BadRequestError):
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=BadRequestError (400)")
            raise ProviderCapabilityError(
                f"BadRequestError (Capability/Request Mismatch): {err_msg}") from exc

        elif isinstance(exc, litellm.Timeout):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=Timeout")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "timeout")
            raise ProviderServiceError(f"Timeout: {err_msg}") from exc

        elif isinstance(exc, (litellm.ServiceUnavailableError, litellm.APIError, litellm.APIConnectionError)):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=ServiceUnavailable/APIError (5xx)")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "service_error")
            raise ProviderServiceError(
                f"ServiceError: {err_msg}") from exc

        else:
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=UnexpectedError: {err_msg}")
            raise ProviderTransientError(
                f"UnexpectedError: {err_msg}") from exc
