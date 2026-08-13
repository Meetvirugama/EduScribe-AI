class ResponseParseError(Exception):
    """
    Raised when raw_response cannot be normalized into the standard dict.
    Treated as a transient error by the LLM Manager (triggers retry).
    """
    pass


class JSONExtractionError(Exception):
    """
    Raised when JSON cannot be extracted or repaired from the LLM response.
    Treated as a transient error to trigger a retry.
    """
    pass


class SchemaValidationError(Exception):
    """
    Raised when Pydantic validation fails on the extracted JSON.
    Treated as a transient error to prompt the LLM again.
    """
    pass
