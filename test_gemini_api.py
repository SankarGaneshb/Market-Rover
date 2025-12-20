"""
Test script to verify Gemini API integration with CrewAI
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents import gemini_llm, create_sentiment_analyzer_agent
from config import GOOGLE_API_KEY

def test_gemini_api_connection():
    """Test if Gemini API is properly configured and accessible"""
    print("=" * 80)
    print("TESTING GEMINI API CONNECTION")
    print("=" * 80)
    
    # Check API key
    if not GOOGLE_API_KEY:
        print("❌ ERROR: GOOGLE_API_KEY is not set in .env file")
        return False
    
    print(f"✅ API Key found (length: {len(GOOGLE_API_KEY)})")
    
    # Test basic LLM call
    try:
        print("\n🔬 Testing basic Gemini LLM call...")
        response = gemini_llm.invoke("What is 2+2? Answer with just the number.")
        print(f"✅ Response: {response.content}")
        
        # Test agent creation with LLM
        print("\n🔬 Testing agent creation with Gemini LLM...")
        agent = create_sentiment_analyzer_agent()
        print(f"✅ Agent created: {agent.role}")
        print(f"   - LLM model: {agent.llm.model_name if hasattr(agent.llm, 'model_name') else 'Unknown'}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Gemini API is working correctly!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. API key not activated")
        print("  3. Network connection issues")
        print("  4. Rate limit exceeded")
        return False

if __name__ == "__main__":
    success = test_gemini_api_connection()
    sys.exit(0 if success else 1)
