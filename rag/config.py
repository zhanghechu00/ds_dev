import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
# Using the same Deepseek model as backend.py
BASE_URL = "https://api.deepseek.com/v1/chat/completions" 
MODEL_NAME = "deepseek-chat"
