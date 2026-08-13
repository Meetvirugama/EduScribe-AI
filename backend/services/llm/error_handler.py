import logging
import litellm
from .base_provider import ProviderTransientError, ProviderPermanentError
from .pipeline import RequestContext

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Translates raw LiteLLM exceptions into robust Provider exceptions."""

    @staticmethod
    def handle_litellm_error(
            exc: Exception, provider: str, model: str, context: RequestContext,
            key_manager: "KeyManager" = None, api_key: str = None) -> None:
        err_msg = str(exc)
        req_id = context.request_id
        task_val = context.task.value

        if isinstance(exc, litellm.RateLimitError):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=RateLimitError (429)")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "rate_limit")
            raise ProviderTransientError(f"RateLimitError: {err_msg}") from exc

        elif isinstance(exc, litellm.AuthenticationError):
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=AuthenticationError (401)")
            if key_manager and api_key:
                key_manager.mark_key_exhausted(provider, api_key, "auth")
            raise ProviderPermanentError(
                f"AuthenticationError: {err_msg}") from exc

        elif isinstance(exc, litellm.BadRequestError):
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | task={task_val} | provider={provider} | model={model} | reason=BadRequestError (400)")
            raise ProviderPermanentError(
                f"BadRequestError: {err_msg}") from exc

        elif isinstance(exc, litellm.Timeout):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=Timeout")
            raise ProviderTransientError(f"Timeout: {err_msg}") from exc

        elif isinstance(exc, litellm.ServiceUnavailableError):
            logger.warning(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=ServiceUnavailable")
            raise ProviderTransientError(
                f"ServiceUnavailable: {err_msg}") from exc

        else:
            logger.error(
                f"LLM_REQUEST_FAILED | req_id={req_id} | provider={provider} | model={model} | reason=UnexpectedError: {err_msg}")
            raise ProviderTransientError(
                f"UnexpectedError: {err_msg}") from exc
