
import requests

API_KEY = "AIzaSyA2uYjzPxb7bpAgvd4xr8dO-NZSW9EttgE"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

headers = {
    "Content-Type": "application/json"
}

data = {
    "contents": [
        {
            "parts": [
                {"text": "Hello Gemini, are you working?"}
            ]
        }
    ]
}

try:
    response = requests.post(URL, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    print("✅ Gemini response:")
    print(response.json())
except requests.exceptions.RequestException as e:
    print("❌ Gemini API failed:", e)
