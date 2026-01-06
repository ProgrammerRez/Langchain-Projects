import logging
from pathlib import Path
from steps.File_Classification import file_extraction_workflow, create_classification_workflow
from steps.Validation import validate_document, create_validation_chain
from state import TriageState
from langchain_groq import ChatGroq
from prompts import CLASSIFICAION_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
PDF_PATH = Path("Data/Purchase-Order-Sample-.pdf")  # Replace with your PDF
DOCUMENT_ID = "demo_doc_001"

# --- DEMO FUNCTION ---
def run_demo_pipeline(pdf_path: Path):
    if not pdf_path.exists():
        logging.error(f"File not found: {pdf_path}")
        return

    logging.info("🚀 Starting demo pipeline")

    # --- INITIAL STATE ---
    initial_state: TriageState = {
        "document_id": DOCUMENT_ID,
        "document_content": None,  # Will be filled after extraction
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {}
    }

    try:
        # --- CREATE LLM AND CLASSIFICATION WORKFLOW ---
        llm = ChatGroq(model='llama-3.3-70b-versatile', temperature=0.0)
        classification_agent = create_classification_workflow(llm, CLASSIFICAION_PROMPT)

        # --- EXTRACT FILE CONTENT ---
        doc_chunks = file_extraction_workflow(str(pdf_path))
        initial_state["document_content"] = [chunk.page_content for chunk in doc_chunks]

        # --- CLASSIFICATION ---
        classified_state = classification_agent.invoke(initial_state)
        logging.info(f"✅ Classification complete | type={classified_state['document_type']} | confidence={classified_state['confidence_score']:.3f}")

        # --- VALIDATION ---
        logging.info("🔍 Starting validation...")
        validation_chain = create_validation_chain()

        # Build extracted signals for demo (first few chunks)
        extracted_signals = {"text_snippet": "\n".join(initial_state["document_content"][:3])} if initial_state["document_content"] else {}

        validation_result = validate_document(
            validated_label=classified_state["document_type"],
            classifier_confidence=classified_state["confidence_score"],
            ambiguous=classified_state["confidence_score"] < 0.8
                      or len(classified_state["classification_details"].get("alternative_types", [])) > 1,
            extracted_signals=extracted_signals,
            chain=validation_chain
        )

        logging.info(f"✅ Validation complete | decision={validation_result.validation_decision}")
        logging.info(f"Matched rules: {validation_result.matched_rules}")
        logging.info(f"Missing rules: {validation_result.missing_required_rules}")
        logging.info(f"Forbidden hits: {validation_result.forbidden_rule_hits}")
        logging.info(f"Justification: {validation_result.justification}")

    except Exception as e:
        logging.exception("🔥 Demo pipeline failed")


if __name__ == "__main__":
    run_demo_pipeline(PDF_PATH)
