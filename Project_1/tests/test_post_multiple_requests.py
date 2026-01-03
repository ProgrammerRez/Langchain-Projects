import requests

url = "http://127.0.0.1:5000/classify"

params = {
    "path": "D:/Side-Projects/Langchain Projects/Project_1/Data/sample-invoice.pdf"  # real PDF path on server
}

payload = {
    "document_id": "doc_001"
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


try:
    response1 = requests.post(
        url,
        params=params,
        json=payload,
        timeout=10
    )
    response1.raise_for_status()

    print("Status:", response1.status_code)
    print("Response:", response1.json())

except requests.exceptions.RequestException as e:
    print("Request failed:", e)


try:
    response2 = requests.post(
        url,
        params=params,
        json=payload,
        timeout=10
    )
    response2.raise_for_status()

    print("Status:", response2.status_code)
    print("Response:", response2.json())

except requests.exceptions.RequestException as e:
    print("Request failed:", e)


try:
    response3 = requests.post(
        url,
        params=params,
        json=payload,
        timeout=10
    )
    response3.raise_for_status()

    print("Status:", response3.status_code)
    print("Response:", response3.json())

except requests.exceptions.RequestException as e:
    print("Request failed:", e)
