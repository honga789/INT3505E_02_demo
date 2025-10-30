import requests

BASE = "http://localhost:5000"
books = [
    {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008, "tags": ["software"]},
    {"title": "Design Patterns", "author": "Erich Gamma et al.", "year": 1994, "tags": ["architecture"]},
    {"title": "The Pragmatic Programmer", "author": "Andy Hunt", "year": 1999, "tags": ["craft"]},
    {"title": "Introduction to Algorithms", "author": "Cormen et al.", "year": 2009, "tags": ["algorithms"]},
]

for b in books:
    r = requests.post(f"{BASE}/books", json=b)
    print(r.status_code, r.json())

print("All books:", requests.get(f"{BASE}/books").json())
