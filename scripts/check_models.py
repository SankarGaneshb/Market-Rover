
import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment.")
        exit(1)
    
    print(f"🔑 Using API Key: {api_key[:5]}...{api_key[-3:]}")
    
    try:
        genai.configure(api_key=api_key)
        
        print("\n📡 Connecting to Google API to list available models...")
        models = list(genai.list_models())
        
        found_any = False
        print("\n✅ Available Models for your Key:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
                found_any = True
                
        if not found_any:
            print("\n⚠️ No 'generateContent' models found. Check if 'Generative Language API' is enabled in your Google Cloud Console.")
        else:
            print("\n✨ Success! Use one of the names above in your agents.py file.")
    
    except Exception as e:
        print(f"\n❌ API Connection Failed:")
        print(e)

if __name__ == "__main__":
    main()
