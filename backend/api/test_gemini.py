import os
from pathlib import Path
from dotenv import dotenv_values
from google import genai

# Locate backend/.env
env_path = Path(__file__).resolve().parents[1] / ".env"

config = dotenv_values(env_path)
api_key = config.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing from backend/.env")

print("API key found:", bool(api_key))
print("API key length:", len(api_key))

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Explain GradMap in one sentence."
    )

    print("\nGemini connection successful!")
    print(response.text)

except Exception as e:
    print("\nGemini connection failed!")
    print(type(e).__name__, str(e))