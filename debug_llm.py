import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment.")
        return

    genai.configure(api_key=api_key)

    print("Checking available models...")
    try:
        seen = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                seen = True
        if not seen:
            print("⚠️ No models found with 'generateContent' capability.")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

    print("\nTesting Generation with 'gemini-1.5-flash'...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, are you working?")
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed 'gemini-1.5-flash': {e}")
        
    print("\nTesting Generation with 'models/gemini-1.5-flash' (explicit prefix)...")
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content("Hello, are you working?")
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed 'models/gemini-1.5-flash': {e}")

if __name__ == "__main__":
    test_gemini()
