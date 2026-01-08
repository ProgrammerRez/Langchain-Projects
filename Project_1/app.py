# app.py
from logger import logger
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import uvicorn
from steps.Pipeline import build_document_pipeline
from state import TriageState

# -------------------------
# CONFIG
# -------------------------

app = FastAPI(title="Document Classification Pipeline")

# -------------------------
# BUILD PIPELINE ONCE
# -------------------------
pipeline = build_document_pipeline()

# -------------------------
# TEMP DIR FOR UPLOADED FILES
# -------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# -------------------------
# ROUTE: Health check
# -------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# -------------------------
# ROUTE: Process PDF
# -------------------------
@app.post("/classify")
def classify_pdf(path:str):
    # Generate unique filename
    file_id = str(uuid.uuid4())

    # Initialize TriageState
    state: TriageState = {
        "document_id": file_id,
        'file_path': path,
        "document_content": None,
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {},
    }

    # Run pipeline
    try:
        result = pipeline(state)
        response = {
            "route": result.get("route"),
            "document_type": state.get("document_type"),
            "confidence_score": state.get("confidence_score"),
            "classification_details": state.get("classification_details"),
        }

        # Include validation results if available
        if "validation" in result:
            v = result["validation"]
            response["validation"] = {
                "decision": v.validation_decision,
                "matched_rules": v.matched_rules,
                "missing_required_rules": v.missing_required_rules,
                "forbidden_hits": v.forbidden_rule_hits,
                "justification": v.justification,
            }

        # Include error if any
        if "error" in result:
            response["error"] = str(result["error"])

        return response

    except Exception as e:
        logger.exception("Pipeline execution failed")
        return JSONResponse(
            status_code=500,
            content={"error": "Pipeline failed", "details": str(e)},
        )

if __name__=='__main__':
    uvicorn.run(app=app,host='127.0.0.1',port=5000)