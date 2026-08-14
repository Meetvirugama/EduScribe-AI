class TranscriptPipelineError(Exception):
    """Base exception for transcript processing."""

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.retryable = retryable


class InvalidURLError(TranscriptPipelineError):

    def __init__(self, message: str):
        super().__init__(
            "INVALID_URL",
            message,
            False,
        )


class UnsupportedSourceError(TranscriptPipelineError):

    def __init__(self, message: str):
        super().__init__(
            "UNSUPPORTED_SOURCE",
            message,
            False,
        )


class MetadataAcquisitionError(TranscriptPipelineError):

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool,
    ):
        super().__init__(
            code,
            message,
            retryable,
        )


class CaptionDiscoveryError(TranscriptPipelineError):

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
    ):
        super().__init__(
            code,
            message,
            retryable,
        )


class TranscriptValidationError(TranscriptPipelineError):

    def __init__(self, message: str):
        super().__init__(
            "TRANSCRIPT_INVALID",
            message,
            False,
        )


class ExportError(TranscriptPipelineError):

    def __init__(
        self,
        message: str,
        retryable: bool = True,
    ):
        super().__init__(
            "EXPORT_FAILED",
            message,
            retryable,
        )
