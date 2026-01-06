"""
Custom exceptions for the document classification + validation pipeline.

These are DOMAIN-LEVEL errors.
They are designed to drive routing, retries, fallbacks, and human review —
not just crash the system.
"""

# =========================
# Base Exception
# =========================

class ClassificationPipelineError(Exception):
    """
    Base class for all pipeline-level exceptions.
    Catch ONLY this at the orchestration / agent boundary.
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
    """Raised when the file type is not supported by the pipeline."""
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
    """Raised when an LLM or model invocation fails, times out, or returns invalid output."""
    error_code = "MODEL_INVOCATION_FAILED"


class InvalidModelResponseError(ModelInvocationError):
    """
    Raised when the LLM responds but violates the expected schema.
    """
    error_code = "INVALID_MODEL_RESPONSE"


# =========================
# State Errors (CRITICAL)
# =========================

class InvalidPipelineStateError(ClassificationPipelineError):
    """
    Raised when the TriageState is missing required fields
    or contains invalid values.
    """

    error_code = "INVALID_PIPELINE_STATE"


class MissingStateFieldError(InvalidPipelineStateError):
    """Raised when a required state key is missing."""
    error_code = "MISSING_STATE_FIELD"


# =========================
# Classification Errors
# =========================

class ClassificationError(ClassificationPipelineError):
    """Raised when classification logic fails."""
    error_code = "CLASSIFICATION_FAILED"


class LowConfidenceClassificationError(ClassificationError):
    """
    Raised when classification confidence is below the acceptable threshold.
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
# Validation Errors
# =========================

class ValidationError(ClassificationPipelineError):
    """
    Raised when validation logic fails or produces an invalid result.
    """
    error_code = "VALIDATION_FAILED"


class RuleEvaluationError(ValidationError):
    """
    Raised when validation rules cannot be evaluated
    due to malformed inputs or missing signals.
    """
    error_code = "RULE_EVALUATION_FAILED"


class AmbiguousValidationResultError(ValidationError):
    """
    Raised when validation cannot reach a decisive outcome.
    """
    error_code = "AMBIGUOUS_VALIDATION"


# =========================
# Routing / Decision Errors
# =========================

class RoutingDecisionError(ClassificationPipelineError):
    """
    Raised when the system cannot determine the next routing step.
    """
    error_code = "ROUTING_DECISION_FAILED"
