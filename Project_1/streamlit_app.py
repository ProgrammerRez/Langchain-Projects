import uuid
from pathlib import Path
import streamlit as st

from logger import logger
from steps.Pipeline import build_document_pipeline
from state import TriageState

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(
    page_title="Document Classification Pipeline",
    layout="centered",
)

st.title("📄 Document Classification Pipeline")

# -------------------------
# BUILD PIPELINE ONCE
# -------------------------
@st.cache_resource
def load_pipeline():
    return build_document_pipeline()

pipeline = load_pipeline()

# -------------------------
# UPLOAD DIR
# -------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# -------------------------
# FILE UPLOAD
# -------------------------
uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    accept_multiple_files=False,
)

run_btn = st.button("Run Classification")

# -------------------------
# PROCESS
# -------------------------
if run_btn:
    if uploaded_file is None:
        st.error("Upload a PDF file first.")
        st.stop()

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{uploaded_file.name}"

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info(f"File saved: {file_path.name}")

    # Initialize state
    state: TriageState = {
        "document_id": file_id,
        "file_path": str(file_path),
        "document_content": None,
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {},
    }

    # Run pipeline
    with st.spinner("Running classification pipeline..."):
        try:
            result = pipeline(state)

            st.success("Pipeline executed successfully")

            # -------------------------
            # RESULTS
            # -------------------------
            st.subheader("Results")

            st.json({
                "route": result.get("route"),
                "document_type": state.get("document_type"),
                "confidence_score": state.get("confidence_score"),
                "classification_details": state.get("classification_details"),
            })

            # -------------------------
            # VALIDATION (OPTIONAL)
            # -------------------------
            if "validation" in result:
                v = result["validation"]
                st.subheader("Validation")

                st.json({
                    "decision": v.validation_decision,
                    "matched_rules": v.matched_rules,
                    "missing_required_rules": v.missing_required_rules,
                    "forbidden_hits": v.forbidden_rule_hits,
                    "justification": v.justification,
                })

            # -------------------------
            # PIPELINE ERROR (LOGIC LEVEL)
            # -------------------------
            if "error" in result:
                st.error(str(result["error"]))

        except Exception as e:
            logger.exception("Pipeline execution failed")
            st.error("Pipeline failed")
            st.exception(e)
