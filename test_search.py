import requests
r = requests.post(
    "http://localhost:8000/api/search",
    json={"query": "квантовое сжатие моделей", "limit": 15},
    timeout=300,
)
print(r.status_code)
print(r.json())