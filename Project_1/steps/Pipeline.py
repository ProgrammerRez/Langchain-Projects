"""
pipeline.py

Single-entry document pipeline.
Classification, validation, and routing are wired ONCE.
"""

from logger import logger
from langchain_groq import ChatGroq

from state import TriageState
from steps.File_Classification import file_extraction_workflow
from steps.Validation import create_validation_chain, validate_document
from steps.Routing import route
from state import DocumentClassification
from prompts import CLASSIFICAION_PROMPT
from exceptions import ClassificationPipelineError


def build_document_pipeline():
    """
    Builds the document pipeline ONCE and returns a callable.

    This prevents:
    - repeated LLM instantiation
    - repeated chain construction
    - hidden state bugs

    Returns:
        function(state: TriageState) -> dict
    """

    logger.info("🧠 Initializing document pipeline (one-time setup)")

    # -------------------------
    # SHARED LLM
    # -------------------------
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0,
    )

    # -------------------------
    # SHARED CHAINS
    # -------------------------
    classifier = llm.with_structured_output(DocumentClassification)
    validation_chain = create_validation_chain()

    # =========================
    # PIPELINE FUNCTION
    # =========================
    def pipeline(state: TriageState) -> dict:
        """
        Executes the full pipeline on a TriageState.

        Steps:
        1. Extraction
        2. Classification (two-pass)
        3. Validation
        4. Routing decision
        """

        try:
            # -------------------------
            # EXTRACTION
            # -------------------------
            chunks = file_extraction_workflow(state["file_path"])
            state["document_content"] = chunks

            content_str = "\n".join(
                c.page_content if hasattr(c, "page_content") else str(c)
                for c in chunks
            )

            # -------------------------
            # CLASSIFICATION (PASS 1)
            # -------------------------
            quick = classifier.invoke([
                ("system", "Classify this document quickly."),
                ("human", content_str[:2000]),
            ])

            if quick.confidence >= 0.8:
                state["document_type"] = quick.document_type
                state["confidence_score"] = quick.confidence
                state["classification_details"] = {
                    "pass": 1,
                    "reasoning": quick.reasoning,
                    "key_indicators": quick.key_indicators,
                    "alternative_types": quick.alternative_types,
                    "ambiguous": False,
                }
            else:
                # -------------------------
                # CLASSIFICATION (PASS 2)
                # -------------------------
                detailed = classifier.invoke([
                    ("system", CLASSIFICAION_PROMPT),
                    ("human", content_str),
                ])

                ambiguous = (
                    detailed.confidence < 0.8
                    or len(detailed.alternative_types) > 2
                )

                state["document_type"] = detailed.document_type
                state["confidence_score"] = detailed.confidence
                state["classification_details"] = {
                    "pass": 2,
                    "reasoning": detailed.reasoning,
                    "key_indicators": detailed.key_indicators,
                    "alternative_types": detailed.alternative_types,
                    "ambiguous": ambiguous,
                }

            # -------------------------
            # VALIDATION
            # -------------------------
            extracted_signals = {
                "text_snippet": content_str[:1500]
            }

            validation = validate_document(
                validated_label=state["document_type"],
                classifier_confidence=state["confidence_score"],
                ambiguous=state["classification_details"]["ambiguous"],
                extracted_signals=extracted_signals,
                chain=validation_chain,
            )

            # -------------------------
            # ROUTING
            # -------------------------
            decision = route(state)

            return {
                "state": state,
                "validation": validation,
                "route": decision,
            }

        except ClassificationPipelineError as e:
            decision = route(state, error=e)
            return {
                "state": state,
                "error": e,
                "route": decision,
            }

    return pipeline
