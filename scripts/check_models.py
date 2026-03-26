
import os
from google import genai
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
        # Use the new Client-based SDK
        client = genai.Client(api_key=api_key)
        
        print("\n📡 Connecting to Google API to list available models...")
        # The new SDK uses client.models.list()
        # It's an iterator, so we convert to list for verification
        models = list(client.models.list())
        
        found_any = False
        print("\n✅ Available Models for your Key:")
        for m in models:
            # Check supported generation methods (in the new SDK, this is accessible via model properties)
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
