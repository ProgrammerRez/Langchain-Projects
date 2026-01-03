from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from langchain_groq import ChatGroq
from steps.File_Classification import classify_docs
from prompts import CLASSIFICAION_PROMPT
from logger import logger
from exceptions import (
    ClassificationError,
    FileIngestionError,
    TextExtractionError,
    OCRFailureError,
    ModelInvocationError,
)

class ClassificationRequest(BaseModel):
    document_id: str

app = FastAPI(title="Document Classification API")

def normalize_result(result):
    return {
        "document_type": result.get("document_type"),
        "confidence_score": result.get("confidence_score", 0),
        "ambiguous": result.get("ambiguous", False),
        "classification_details": result.get("classification_details", {}),
    }

@app.post("/classify")
async def classify_document(request: ClassificationRequest, path: str):
    """
    Classifies the whole document and returns the result.
    """
    llm = ChatGroq(model="llama-3.3-70b-versatile")

    initial_state = {
        "document_id": request.document_id,
        "document_content": "",
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {},
        "ambiguous": False,
    }

    try:
        # Call your classification pipeline
        result = normalize_result(classify_docs(
            file_path=Path(path),
            llm=llm,
            system_prompt=CLASSIFICAION_PROMPT,
            input=initial_state
        ))

        logger.info(
            f"📄 Document classified | id={request.document_id} | "
            f"type={result['document_type']} | confidence={result['confidence_score']:.3f} | "
            f"ambiguous={result['ambiguous']}"
        )

        return result

    except FileIngestionError as e:
        logger.error(f"📄 File ingestion failed | {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except OCRFailureError as e:
        logger.error(f"🔍 OCR failed | {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except TextExtractionError as e:
        logger.error(f"📑 Text extraction failed | {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except ModelInvocationError as e:
        logger.error(f"🧠 Model failure | {e}")
        raise HTTPException(status_code=503, detail=str(e))

    except ClassificationError as e:
        logger.error(f"❌ Classification failed | {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception("🔥 Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = "127.0.0.1"
    port = 5000
    logger.info(f"🚀 Starting server at {host}:{port}")
    uvicorn.run(app=app, host=host, port=port)
