from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from unstructured.partition.pdf import partition_pdf
from langchain_classic.schema import Document
from logger import logging
from state import DocumentClassification, TriageState
from exceptions import (
    FileIngestionError,
    TextExtractionError,
    OCRFailureError,
    ModelInvocationError,
    ClassificationError,
)
import tempfile as tf
import os

def run_ocr(path: str) -> str:
    logging.info("🔄 Running OCR fallback")

    try:
        elements = partition_pdf(filename=path)
        text = "\n".join(el.text for el in elements if hasattr(el, "text"))

        if not text.strip():
            logging.error("❌ OCR produced empty output")
            raise OCRFailureError("OCR returned no readable text")

        logging.info("✅ OCR successful")
        return text

    except OCRFailureError:
        raise

    except Exception as e:
        logging.exception("❌ OCR execution failed")
        raise OCRFailureError(str(e))


def file_extraction_workflow(path: str) -> list[Document]:
    logging.info(f"📄 Starting file extraction: {path}")

    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        logging.exception("❌ Failed to read input file")
        raise FileIngestionError(str(e))

    tmp_path = None

    try:
        fd, tmp_path = tf.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(data)

        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        full_text = "\n".join(doc.page_content for doc in documents)

        if len(full_text.strip()) < 20:
            logging.warning("⚠️ Low text detected — running OCR fallback")
            ocr_text = run_ocr(tmp_path)
            documents = [Document(page_content=ocr_text)]

    except OCRFailureError:
        raise



    except Exception as e:
        logging.exception("❌ Text extraction failed")
        raise TextExtractionError(str(e))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)

    logging.info(f"✅ Extraction complete | chunks={len(chunks)}")
    return chunks



def create_classificatioN_workflow(llm, system_prompt):
    classifier = llm.with_structured_output(DocumentClassification)

    logging.info("🧠 Classification workflow initialized")

    def classify_with_fallback(state: TriageState) -> dict:
        logging.info("🧠 Starting document classification")

        try:
            quick = classifier.invoke(
                [
                    SystemMessage(
                        content="Classify this document type quickly."
                    ),
                    HumanMessage(
                        content=state["document_content"][:2000]
                    ),
                ]
            )
            logging.info(
                f"✅ Pass 1 completed | confidence={quick.confidence:.3f}"
            )

        except Exception as e:
            logging.exception("❌ Model invocation failed (pass 1)")
            raise ModelInvocationError(str(e))

        if quick.confidence >= 0.8:
            return {
                "document_type": quick.document_type,
                "confidence_score": quick.confidence,
                "ambiguous": False,
                "classification_details": {
                    "reasoning": quick.reasoning,
                    "key_indicators": quick.key_indicators,
                    "alternatives": quick.alternative_types,
                    "pass": 1,
                },
            }

        try:
            detailed = classifier.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=state["document_content"]),
                ]
            )
            logging.info(
                f"🔍 Pass 2 completed | confidence={detailed.confidence:.3f}"
            )

        except Exception as e:
            logging.exception("❌ Model invocation failed (pass 2)")
            raise ModelInvocationError(str(e))

        ambiguous = (
            detailed.confidence < 0.8
            or len(detailed.alternative_types) > 2
        )

        return {
            "document_type": detailed.document_type,
            "confidence_score": detailed.confidence,
            "ambiguous": ambiguous,
            "classification_details": {
                "reasoning": detailed.reasoning,
                "key_indicators": detailed.key_indicators,
                "alternatives": detailed.alternative_types,
                "pass": 2,
            },
        }

    builder = StateGraph(TriageState)
    builder.add_node("classify", classify_with_fallback)
    builder.add_edge(START, "classify")
    builder.add_edge("classify", END)

    return builder.compile()


def classify_docs(file_path, llm, system_prompt, input: TriageState):
    logging.info("🚀 Starting classification pipeline")

    try:
        doc_splits = file_extraction_workflow(file_path)

        agent = create_classificatioN_workflow(llm, system_prompt)

        input["document_content"] = "\n".join(
            doc.page_content for doc in doc_splits
        )

        return agent.invoke(input=input)

    except Exception as e:
        logging.exception("🔥 Classification pipeline failed")
        raise ClassificationError(str(e))



# if __name__=='__main__':
    
    
#     llm = ChatGroq(model='llama-3.3-70b-versatile')
    
#     agent = create_classificatioN_workflow(llm, CLASSIFICAION_PROMPT)
    
#     initial_state: TriageState = {
#         "document_id": "doc_001",
#         "document_content": "Invoice #1234\nTotal Amount: $450\nDue Date: 10 Jan 2026",
#         "document_type": None,
#         "confidence_score": 0.0,
#         "classification_details": {}
#     }

#     result = agent.invoke(initial_state)

#     print(result)