import requests

url = "http://127.0.0.1:5000/items/"  

initial_state = {
    "document_id": "doc_001",
    "document_content": "Invoice #1234\nTotal Amount: $450\nDue Date: 10 Jan 2026",
    "document_type": None,
    "confidence_score": 0.0,
    "classification_details": {}
}

try:
    response = requests.post(url, json=initial_state, timeout=5)
    response.raise_for_status()  # raises exception if 4xx/5xx
    print("Status:", response.status_code)
    print("Response:", response.json())
except requests.exceptions.RequestException as e:
    print("Request failed:", e)