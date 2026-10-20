from google import genai
import os
from dotenv import load_dotenv

def test_gemini_connection():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        return False
        
    try:
        # Create client instance with correct SDK
        client = genai.Client(api_key=api_key)
        
        # Test prompt
        test_prompt = "Convert this command to shell: install python"
        
        # Generate response
        response = client.models.generate_content(
            model=model_name,
            contents=test_prompt
        )
        
        print("API Connection: Success")
        print("Response:", response.text)
        return True
        
    except Exception as e:
        print(f"Error testing Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_connection()
