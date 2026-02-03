import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    # try hardcoded path if needed, or just fail
    print("Error: GOOGLE_API_KEY not found.")
else:
    genai.configure(api_key=api_key)
    print("Available GenAI Models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
