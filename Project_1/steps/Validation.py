"""
File: validation.py

Purpose:
--------
Rule-based validation of document classification results.

Critical Architectural Rule:
----------------------------
This module NEVER receives raw document text.

Validation operates ONLY on:
- classifier outputs
- extracted signals
- predefined rule sets

This guarantees token safety and deterministic behavior.
"""

from logger import logger
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from state import DocumentValidation, DOCUMENT_RULES
from prompts import VALIDATION_PROMPT




# =========================
# CHAIN CREATION
# =========================
def create_validation_chain():
    """
    Create a validation chain that evaluates classifier output
    against rule definitions using structured evidence only.

    Returns:
        Runnable chain producing DocumentValidation.
    """
    logger.info("Creating validation chain...")

    prompt = ChatPromptTemplate.from_messages([
        VALIDATION_PROMPT,
        """
VALIDATED LABEL:
{validated_label}

CLASSIFIER CONFIDENCE:
{classifier_confidence}

AMBIGUOUS FLAG:
{ambiguous}

VALIDATION RULES:
{rules}

EXTRACTED SIGNALS:
{extracted_signals}

TASK:
Validate the document against the rules.

STRICT CONSTRAINTS:
- DO NOT re-classify the document
- DO NOT infer missing data
- Base decisions ONLY on extracted signals
- Reference rules explicitly

Return:
- validation_decision: VALID | WEAK | INVALID
- matched_rules
- missing_required_rules
- forbidden_rule_hits
- justification (concise, factual)
"""
    ])
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0
    )
    logger.info("Validation chain created successfully.")
    return prompt | llm.with_structured_output(DocumentValidation)


# =========================
# VALIDATION EXECUTION
# =========================
def validate_document(
    *,
    validated_label: str,
    classifier_confidence: float,
    ambiguous: bool,
    extracted_signals: Dict[str, Any],
    chain
) -> DocumentValidation:
    """
    Validate a classified document using structured signals only.

    Args:
        validated_label (str): Label produced by the classifier.
        classifier_confidence (float): Confidence score from classification.
        ambiguous (bool): Ambiguity flag from classification.
        extracted_signals (Dict[str, Any]): Structured evidence extracted earlier.
        chain: Validation chain created by create_validation_chain().

    Returns:
        DocumentValidation: Structured validation result.
    """
    logger.info(
        "Starting document validation | label=%s confidence=%.2f ambiguous=%s",
        validated_label,
        classifier_confidence,
        ambiguous
    )

    rules = DOCUMENT_RULES.get(validated_label, [])
    logger.debug("Loaded rules for label %s: %s", validated_label, rules)

    try:
        result = chain.invoke({
            "validated_label": validated_label,
            "classifier_confidence": classifier_confidence,
            "ambiguous": ambiguous,
            "rules": rules,
            "extracted_signals": extracted_signals,
        })
        logger.info("Validation completed | decision=%s", result.validation_decision)
        return result
    except Exception:
        logger.exception("Validation chain invocation failed")
        raise
