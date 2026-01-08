"""
File_Classification.py

Purpose:
--------
Handles extraction, chunking, classification (two-pass), and OCR fallback
for PDF documents using your TriageState and DocumentClassification.
"""

from typing import List
import tempfile as tf
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, state
from langchain_groq import ChatGroq
from langchain_classic.schema import Document
from logger import logger
from prompts import CLASSIFICAION_PROMPT
from state import DocumentClassification, TriageState
from exceptions import (
    FileIngestionError,
    TextExtractionError,
    OCRFailureError,
    ModelInvocationError,
    ClassificationError,
)

# -------------------------
# OCR fallback
# -------------------------
def run_ocr(path: str) -> str:
    from unstructured.partition.pdf import partition_pdf
    """
    OCR Fallback: extracts text from PDF using unstructured.partition.pdf.
    """
    logger.info("🔄 Running OCR fallback")
    try:
        elements = partition_pdf(
            filename=path,
            infer_table_structure=False,
            strategy="fast",  # CRITICAL
        )
        text = "\n".join(el.text for el in elements if hasattr(el, "text"))
        if not text.strip():
            raise OCRFailureError("OCR returned no readable text")
        logger.info("✅ OCR successful")
        return text
    except OCRFailureError:
        raise
    except Exception as e:
        logger.exception("❌ OCR execution failed")
        raise OCRFailureError(str(e))


# -------------------------
# File extraction
# -------------------------
def file_extraction_workflow(path: str) -> List[Document]:
    """
    Extract text from PDF using PyPDFLoader, falls back to OCR if necessary.
    Splits text into chunks for classification.
    """
    logger.info(f"📄 Extracting file: {path}")
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        logger.exception("❌ Failed to read input file")
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
            logger.warning("⚠️ Low text detected — running OCR fallback")
            ocr_text = run_ocr(tmp_path)
            documents = [Document(page_content=ocr_text)]

    except OCRFailureError:
        raise
    except Exception as e:
        logger.exception("❌ Text extraction failed")
        raise TextExtractionError(str(e))

    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    logger.info(f"✅ Extraction complete | chunks={len(chunks)}")
    return chunks


# -------------------------
# Classification workflow
# -------------------------
def create_classification_workflow(llm, system_prompt) -> state.CompiledStateGraph:
    """
    Creates the classification workflow graph using your DocumentClassification schema.
    """

    classifier = llm.with_structured_output(DocumentClassification)
    logger.info("🧠 Classification workflow initialized")

    def classify_with_fallback(state: TriageState) -> dict:
        logger.info("🧠 Starting document classification")

        # Serialize content to string for Groq
        if state["document_content"] and isinstance(state["document_content"], list):
            content_str = ""
            for doc in state["document_content"]:
                if hasattr(doc, "page_content"):
                    content_str += doc.page_content + "\n"
                else:
                    content_str += str(doc) + "\n"
        else:
            content_str = str(state["document_content"] or "")

        # Pass 1: quick classification
        try:
            quick = classifier.invoke([
                SystemMessage(content="Classify this document type quickly."),
                HumanMessage(content=content_str[:2000])  # slice string safely
            ])
            logger.info(f"✅ Pass 1 completed | confidence={quick.confidence:.3f}")
        except Exception as e:
            logger.exception("❌ Model invocation failed (pass 1)")
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

        # Pass 2: detailed classification
        try:
            detailed = classifier.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=content_str)  # full string
            ])
            logger.info(f"🔍 Pass 2 completed | confidence={detailed.confidence:.3f}")
        except Exception as e:
            logger.exception("❌ Model invocation failed (pass 2)")
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


# -------------------------
# Main classification function
# -------------------------
def classify_docs(file_path: str, state: TriageState) -> dict:
    """
    Full classification pipeline:
    1. Extract text from file (OCR fallback)
    2. Chunk text
    3. Run two-pass classification
    4. Returns updated TriageState dict
    """
    logger.info("🚀 Starting classification pipeline")
    try:
        doc_splits = file_extraction_workflow(file_path)
        state["document_content"] = doc_splits

        # Create agent once
        llm = ChatGroq(model='llama-3.3-70b-versatile')
        agent = create_classification_workflow(llm=llm, system_prompt=CLASSIFICAION_PROMPT)

        return agent.invoke(input=state)

    except Exception as e:
        logger.exception("🔥 Classification pipeline failed")
        raise ClassificationError(str(e))
