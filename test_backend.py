import requests

response = requests.post(
    "http://127.0.0.1:8000/ask",
    json={"query": "What are COA basic IO operations?"}
)
print("Status Code:", response.status_code)
if response.status_code == 200:
    print("Answer:", response.json().get("answer", "No answer field found"))
else:
    print("Response:", response.text)
