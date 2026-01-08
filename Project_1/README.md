# Document Classification Pipeline

## Overview
This project implements a sophisticated document classification pipeline using FastAPI, LangChain, and LangGraph. It processes PDF documents (Invoices, Contracts, W2 Forms, Medical Records, Insurance Claims, Purchase Orders) and classifies them using LLMs (Groq/Llama-3). It features failover mechanisms including OCR (Optical Character Recognition) for low-quality documents and a two-pass classification system for high accuracy.

## Project Structure

```
Project_1/
├── app.py                  # FastAPI application entry point and API endpoints
├── template.py             # Project scaffolding script
├── requirements.txt        # Python dependencies
├── steps/                  # Core pipeline logic
│   ├── File_Classification.py  # Extraction, Chunking, and Classification workflow
│   ├── Pipeline.py             # Pipeline construction
│   ├── Routing.py              # Routing logic based on classification
│   └── Validation.py           # Document validation logic
├── state/                  # State definitions and Data Models
│   └── __init__.py             # TriageState, DocumentClassification models
├── prompts/                # LLM Prompts
│   └── __init__.py             # Classification and Validation prompts
├── logger/                 # Logging configuration
│   └── __init__.py             # Custom logger setup
├── exceptions/             # Custom exception classes
├── uploads/                # Temporary directory for uploaded files
└── logs/                   # Application logs
```

## Function System
- **File Extraction**: `steps/File_Classification.py` handles PDF loading (PyPDFLoader) and falls back to `unstructured` OCR if text content is insufficient.
- **Classification**: Uses a Graph-based approach (LangGraph) with a two-pass system (Quick & Detailed) to determine document type and confidence.
- **Validation**: Enforces business rules for specific document types (e.g., checking for specific fields in Invoices vs Contracts).
- **API**: `app.py` exposes a REST API to submit documents and receive classification results.

## Setup Instructions

1. **Prerequisites**
   - Python 3.9+
   - API Key for Groq (set as environment variable)

2. **Environment Setup**
   Create a `.env` file or set the environment variable:
   ```bash
   export GROQ_API_KEY="your_groq_api_key_here"
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `unstructured` may require system dependencies like `tesseract-ocr` and `poppler-utils` depending on your OS.*

## Usage

1. **Start the Server**
   ```bash
   python app.py
   ```
   The server will start at `http://127.0.0.1:5000`.

2. **API Documentation**
   Visit `http://127.0.0.1:5000/docs` for the interactive Swagger UI.

3. **Classify a Document**
   Send a POST request to `/classify` with the `path` query parameter pointing to a local PDF file.

   **Example (cURL):**
   ```bash
   curl -X 'POST' \
     'http://127.0.0.1:5000/classify?path=d%3A%2Fpath%2Fto%2Fyour%2Fdocument.pdf' \
     -H 'accept: application/json'
   ```

## Logging
Logs are written to `logs/app.log` with rotation enabled (daily at midnight).
