import requests

url = "http://127.0.0.1:5000/classify"

params = {
    "path": "D:/Side-Projects/Langchain Projects/Project_1/Data/sample-invoice.pdf"  # real PDF path on server
}

payload = {
    "document_id": "doc_001",
    'ambiguous': False
    
}

try:
    response = requests.post(
        url,
        params=params,
        json=payload,
        timeout=10
    )
    response.raise_for_status()

    print("Status:", response.status_code)
    print("Response:", response.json())

except requests.exceptions.RequestException as e:
    print("Request failed:", e)

