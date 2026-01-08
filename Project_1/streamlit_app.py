import streamlit as st
import uuid
from pathlib import Path

from logger import logger
from steps.Pipeline import build_document_pipeline
from state import TriageState

# -------------------------
# PAGE CONFIG
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
# TEMP DIR (OPTIONAL)
# -------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# -------------------------
# INPUT
# -------------------------
st.subheader("Input Document")

file_path = st.text_input(
    "Enter absolute path to PDF/document",
    placeholder="D:/docs/sample.pdf",
)

run_btn = st.button("Run Classification")

# -------------------------
# PROCESS
# -------------------------
if run_btn:
    if not file_path:
        st.error("Provide a valid file path.")
        st.stop()

    if not Path(file_path).exists():
        st.error("File does not exist.")
        st.stop()

    with st.spinner("Running classification pipeline..."):
        file_id = str(uuid.uuid4())

        state: TriageState = {
            "document_id": file_id,
            "file_path": file_path,
            "document_content": None,
            "document_type": None,
            "confidence_score": 0.0,
            "classification_details": {},
        }

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
            # VALIDATION (IF EXISTS)
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
            # ERROR (PIPELINE-LEVEL)
            # -------------------------
            if "error" in result:
                st.error(str(result["error"]))

        except Exception as e:
            logger.exception("Pipeline execution failed")
            st.error("Pipeline failed")
            st.exception(e)
