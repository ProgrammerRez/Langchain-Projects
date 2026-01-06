from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from pathlib import Path

from steps.File_Classification import classify_docs
from steps.Validation import create_validation_chain, validate_document
from logger import logger
from exceptions import (
    ClassificationError,
    FileIngestionError,
    TextExtractionError,
    OCRFailureError,
    ModelInvocationError,
)

# ------------------------
# Request Model
# ------------------------

class ClassificationRequest(BaseModel):
    document_id: str


# ------------------------
# App
# ------------------------

app = FastAPI(title="Document Classification API")

# Validation chain (must be stateless)
val_llm = create_validation_chain()


# ------------------------
# Helpers
# ------------------------

def normalize_result(result: dict) -> dict:
    return {
        "document_type": result.get("document_type"),
        "confidence_score": result.get("confidence_score", 0.0),
        "ambiguous": result.get("ambiguous", False),
        "classification_details": result.get("classification_details", {}),
        "document_content": result.get("document_content", ""),
    }


# ------------------------
# Endpoint
# ------------------------

@app.post("/classify")
async def classify_document(
    request: ClassificationRequest,
    path: str = Query(..., description="Path to the document file"),
):
    """
    Classifies the whole document and returns the result.
    """

    initial_state = {
        "document_id": request.document_id,
        "document_content": "",
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {},
        "ambiguous": False,
    }

    try:
        # ---- Run heavy work off the event loop ----
        raw_result = await run_in_threadpool(
            classify_docs,
            file_path=Path(path),
            input=initial_state, # type: ignore
        )

        result = normalize_result(raw_result)

        logger.info(
            f"📄 Document classified | id={request.document_id} | "
            f"type={result['document_type']} | "
            f"confidence={result['confidence_score']:.3f} | "
            f"ambiguous={result['ambiguous']}"
        )

        validation = validate_document(
            content=result["document_content"], # type: ignore
            label=result["document_type"],
            confidence=result["confidence_score"],
            ambiguous=result["ambiguous"],
            chain=val_llm,
        )

        return {
            "document_id": request.document_id,
            "document_type": result["document_type"],
            "confidence_score": result["confidence_score"],
            "ambiguous": result["ambiguous"],
            "classification_details": result["classification_details"],
            "validation": validation,
        }

    except FileIngestionError as e:
        logger.error(f"📄 File ingestion failed | {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except (OCRFailureError, TextExtractionError) as e:
        logger.error(f"📑 Text extraction failed | {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except ModelInvocationError:
        logger.error("🧠 Model invocation failed")
        raise HTTPException(status_code=503, detail="Model unavailable")

    except ClassificationError as e:
        logger.error(f"❌ Classification failed | {e}")
        raise HTTPException(status_code=500, detail="Classification failed")

    except Exception:
        logger.exception("🔥 Unexpected server error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


# ------------------------
# Entrypoint
# ------------------------

if __name__ == "__main__":
    import uvicorn

    host = "127.0.0.1"
    port = 5000

    logger.info(f"🚀 Starting server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
