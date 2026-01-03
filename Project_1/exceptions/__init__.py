"""
Custom exceptions for the document classification pipeline.

These exceptions are DOMAIN-LEVEL errors.
They are meant to drive routing decisions, not just crash the system.
"""


# =========================
# Base Exception
# =========================

class ClassificationPipelineError(Exception):
    """
    Base class for all classification pipeline exceptions.
    Catch this at the orchestration / agent level.
    """
    error_code = "PIPELINE_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# =========================
# Ingestion Errors
# =========================

class FileIngestionError(ClassificationPipelineError):
    """Raised when the input file cannot be read, saved, or accessed."""
    error_code = "FILE_INGESTION_FAILED"


class UnsupportedFileTypeError(ClassificationPipelineError):
    """Raised when the file type is not supported."""
    error_code = "UNSUPPORTED_FILE_TYPE"


# =========================
# Extraction Errors
# =========================

class TextExtractionError(ClassificationPipelineError):
    """Raised when text extraction from the document fails."""
    error_code = "TEXT_EXTRACTION_FAILED"


class OCRFailureError(TextExtractionError):
    """Raised when OCR fallback fails or produces unusable text."""
    error_code = "OCR_FAILED"


# =========================
# Model / LLM Errors
# =========================

class ModelInvocationError(ClassificationPipelineError):
    """Raised when a model or LLM call fails or times out."""
    error_code = "MODEL_INVOCATION_FAILED"


# =========================
# Classification Errors
# =========================

class ClassificationError(ClassificationPipelineError):
    """Raised when classification logic fails."""
    error_code = "CLASSIFICATION_FAILED"


class LowConfidenceClassificationError(ClassificationError):
    """
    Raised when classification confidence is below an acceptable threshold.
    """

    error_code = "LOW_CONFIDENCE"

    def __init__(self, confidence: float, threshold: float):
        self.confidence = confidence
        self.threshold = threshold
        message = (
            f"Classification confidence {confidence:.3f} "
            f"is below threshold {threshold:.3f}"
        )
        super().__init__(message)


# =========================
# Routing / Decision Errors
# =========================

class RoutingDecisionError(ClassificationPipelineError):
    """Raised when a routing decision cannot be determined."""
    error_code = "ROUTING_DECISION_FAILED"
