import requests
import json
from .config import API_KEY, BASE_URL, MODEL_NAME

def chat_completion(messages, temperature=0.1):
    if not API_KEY:
        print("Warning: OPENROUTER_API_KEY not found.")
        return ""
        
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM Error: {e}")
        return ""
