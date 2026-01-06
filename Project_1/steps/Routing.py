"""
Routing logic for the document classification pipeline.

This module decides WHAT happens next.
It does not execute models, OCR, or validation.
"""

from logger import logger

from exceptions import (
    ClassificationPipelineError,
    FileIngestionError,
    TextExtractionError,
    OCRFailureError,
    ModelInvocationError,
    InvalidPipelineStateError,
    LowConfidenceClassificationError,
    ValidationError,
    RoutingDecisionError,
)

from state import TriageState, RouteDecision




# =========================
# Core Routing Function
# =========================
def route(
    state: TriageState,
    error: ClassificationPipelineError | None = None,
) -> RouteDecision:
    """
    Decide the next pipeline action based on state and raised error.

    Args:
        state: Current TriageState
        error: Exception raised during the pipeline (if any)

    Returns:
        RouteDecision string
    """
    logger.info("Routing decision requested | state=%s error=%s", state, error)

    try:
        # -------------------------
        # HARD FAILS (developer bugs)
        # -------------------------
        if isinstance(error, InvalidPipelineStateError):
            logger.error("Invalid pipeline state encountered")
            return "FAIL_PIPELINE"

        # -------------------------
        # INGESTION / EXTRACTION
        # -------------------------
        if isinstance(error, (FileIngestionError, TextExtractionError, OCRFailureError)):
            logger.warning("Extraction-related error | retrying")
            return "RETRY_EXTRACTION"

        # -------------------------
        # MODEL FAILURES
        # -------------------------
        if isinstance(error, ModelInvocationError):
            logger.warning("Model invocation error | retrying classification")
            return "RETRY_CLASSIFICATION"

        # -------------------------
        # CLASSIFICATION QUALITY
        # -------------------------
        if isinstance(error, LowConfidenceClassificationError):
            logger.info("Low confidence classification | escalating to human review")
            return "HUMAN_REVIEW"

        # -------------------------
        # VALIDATION FAILURES
        # -------------------------
        if isinstance(error, ValidationError):
            logger.info("Validation error | rejecting document")
            return "REJECT"

        # -------------------------
        # NO ERROR → DECIDE FROM STATE
        # -------------------------
        if not state.get("document_type"):
            raise RoutingDecisionError("Missing document_type in state")

        confidence = state.get("confidence_score", 0.0)
        logger.debug("State confidence_score=%.2f", confidence)

        # Conservative thresholding
        if confidence < 0.6:
            logger.info("Confidence below threshold | escalating to human review")
            return "HUMAN_REVIEW"

        logger.info("Document accepted by routing logic")
        return "ACCEPT"

    except Exception:
        logger.exception("Routing decision failed")
        raise
