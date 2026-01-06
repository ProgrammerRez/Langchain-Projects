import logging
from pathlib import Path

from steps.Pipeline import build_document_pipeline
from state import TriageState

# -------------------------
# CONFIG
# -------------------------
logging.basicConfig(level=logging.INFO)

PDF_PATH = Path("Data/Purchase-Order-Sample-.pdf")
DOCUMENT_ID = "demo_doc_001"


def run_demo():
    if not PDF_PATH.exists():
        logging.error(f"❌ File not found: {PDF_PATH}")
        return

    # -------------------------
    # INITIAL STATE
    # -------------------------
    state: TriageState = {
        "document_id": DOCUMENT_ID,
        "file_path": str(PDF_PATH),
        "document_content": None,
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {},
    }

    # -------------------------
    # BUILD PIPELINE ONCE
    # -------------------------
    pipeline = build_document_pipeline()

    # -------------------------
    # RUN PIPELINE
    # -------------------------
    result = pipeline(state)

    # -------------------------
    # OUTPUT
    # -------------------------
    logging.info("========== PIPELINE RESULT ==========")
    logging.info(f"Route decision: {result['route']}")

    if "validation" in result:
        v = result["validation"]
        logging.info(f"Validation decision: {v.validation_decision}")
        logging.info(f"Matched rules: {v.matched_rules}")
        logging.info(f"Missing rules: {v.missing_required_rules}")
        logging.info(f"Forbidden hits: {v.forbidden_rule_hits}")
        logging.info(f"Justification: {v.justification}")

    if "error" in result:
        logging.error(f"Pipeline error: {result['error']}")


if __name__ == "__main__":
    run_demo()
