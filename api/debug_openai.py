# ===== UPDATED DEBUG SCRIPT - TEST OPENAI CONNECTION (v1.0+ Compatible) =====
# Save this as api/debug_openai.py and run it to test your setup

import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_connection():
    """Test OpenAI API connection and configuration"""
    print("🔍 Testing OpenAI Connection...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
    print(f"1. API Key: {'✅ Found' if api_key else '❌ Missing'}")
    
    if not api_key:
        print("\n❌ ERROR: REACT_APP_OPENAI_API_KEY not found in environment")
        print("Please add it to your .env file:")
        print("REACT_APP_OPENAI_API_KEY=sk-proj-your-key-here")
        return False
    
    # Mask the key for security
    masked_key = api_key[:12] + "..." + api_key[-4:] if len(api_key) > 16 else "***"
    print(f"   Key: {masked_key}")
    
    # Set up OpenAI client (NEW v1.0+ syntax)
    client = OpenAI(api_key=api_key)
    
    # Test connection
    try:
        print("\n2. Testing API Connection...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection successful'"}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content
        print(f"   Response: {result}")
        print("   ✅ OpenAI API connection successful!")
        
        # Test roleplay scenario
        print("\n3. Testing Roleplay Scenario...")
        roleplay_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a Manager at a Technology company receiving a cold call.
                    
CRITICAL INSTRUCTIONS:
- Respond naturally and realistically 
- Keep responses short (1-2 sentences)
- Show realistic prospect behavior - skeptical but professional
- Stay in character as a busy business professional

The caller just said: 'Hi, I know this is out of the blue, but may I tell you why I'm calling?'

Respond naturally as the prospect:"""
                },
                {"role": "user", "content": "Respond to this cold call opener."}
            ],
            max_tokens=50,
            temperature=0.8
        )
        
        roleplay_result = roleplay_response.choices[0].message.content
        print(f"   Roleplay Response: {roleplay_result}")
        print("   ✅ Roleplay prompt working!")
        
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        print(f"   ❌ {error_type}: {e}")
        
        # Provide specific guidance based on error type
        if "authentication" in str(e).lower():
            print("   Check your API key is correct and active")
        elif "rate_limit" in str(e).lower():
            print("   Your API key is valid but you've hit the rate limit")
        elif "billing" in str(e).lower():
            print("   Check that your OpenAI account has billing set up")
        else:
            print("   Check your API key and OpenAI account status")
        
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing Environment Configuration...")
    print("=" * 50)
    
    # Check for .env file
    env_file_exists = os.path.exists('.env')
    print(f"1. .env file: {'✅ Found' if env_file_exists else '❌ Missing'}")
    
    if not env_file_exists:
        print("   Create a .env file with your API keys")
    
    # Check all required environment variables
    required_vars = [
        'REACT_APP_OPENAI_API_KEY',
        'REACT_APP_ELEVENLABS_API_KEY',
        'REACT_APP_SUPABASE_URL',
        'REACT_APP_SUPABASE_ANON_KEY'
    ]
    
    print("\n2. Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        status = '✅ Set' if value else '❌ Missing'
        print(f"   {var}: {status}")

def main():
    """Main debug function"""
    print("🚀 Cold Calling Coach - OpenAI Debug Script (v1.0+ Compatible)")
    print("=" * 60)
    
    # Test environment
    test_environment()
    
    # Test OpenAI connection
    success = test_openai_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Your OpenAI setup is working correctly.")
        print("\nNext steps:")
        print("1. Update your openai_service.py to use the new v1.0+ API")
        print("2. Replace your roleplay_engine.py with the updated version")
        print("3. Test the roleplay system")
    else:
        print("❌ Setup issues found. Please fix the errors above.")
        print("\nCommon solutions:")
        print("1. Check your .env file has the correct API key")
        print("2. Verify your OpenAI account has billing set up")
        print("3. Make sure the API key starts with 'sk-proj-' or 'sk-'")
        print("4. If you see 'authentication' errors, double-check your API key")

if __name__ == "__main__":
    main()

# ===== QUICK TEST COMMANDS =====
"""
To run this debug script:

1. Save this file as api/debug_openai.py (replace the old one)
2. Run: python api/debug_openai.py
3. Check the output for any errors

Key changes for OpenAI v1.0+:
- Use: client = OpenAI(api_key=api_key)
- Use: client.chat.completions.create() instead of openai.ChatCompletion.create()
- Error handling is now based on standard Python exceptions

If you still see errors:
- "API Key Missing": Add REACT_APP_OPENAI_API_KEY to .env file
- "Authentication Error": Check your API key is correct
- "Rate Limit Error": Wait a few minutes or check billing
- "Invalid Request Error": Check the model name is correct
"""