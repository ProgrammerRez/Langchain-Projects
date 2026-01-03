import requests
from threading import Thread
from pathlib import Path

# List of PDFs to classify
pdf_paths = [
    "D:/Side-Projects/Langchain Projects/Project_1/Data/sample-invoice.pdf",
    "D:/Side-Projects/Langchain Projects/Project_1/Data/Purchase-Order-Sample-.pdf",
    "D:/Side-Projects/Langchain Projects/Project_1/Data/Sample-filled-in-MR.pdf",
]

# API endpoint (non-streaming version)
url = "http://127.0.0.1:5000/classify"

def classify_document(doc_id, path):
    payload = {"document_id": doc_id}
    params = {"path": path}

    try:
        response = requests.post(url, params=params, json=payload, timeout=180)  # longer timeout for bigger PDFs
        response.raise_for_status()
        result = response.json()

        print(f"[{doc_id}] Classification complete for {path}")
        print(f"[{doc_id}] Result: {result}\n")

    except requests.exceptions.RequestException as e:
        print(f"[{doc_id}] Request failed: {e}")


threads = []

# Launch each PDF classification in a separate thread
for i, path in enumerate(pdf_paths):
    doc_id = f"doc_{i+1}"
    thread = Thread(target=classify_document, args=(doc_id, path))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()

print("✅ All classification requests complete")
