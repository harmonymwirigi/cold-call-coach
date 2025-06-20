# ===== DEBUG_ROLEPLAY_11.PY - Test OpenAI and Services =====

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment variables"""
    print("=== ENVIRONMENT TEST ===")
    
    # Check OpenAI API key
    openai_key = os.getenv('REACT_APP_OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API Key: {openai_key[:8]}...{openai_key[-4:]}")
    else:
        print("❌ OpenAI API Key: NOT FOUND")
        print("   Please set REACT_APP_OPENAI_API_KEY in your .env file")
    
    # Check ElevenLabs API key
    elevenlabs_key = os.getenv('REACT_APP_ELEVENLABS_API_KEY')
    if elevenlabs_key:
        print(f"✅ ElevenLabs API Key: {elevenlabs_key[:8]}...{elevenlabs_key[-4:]}")
    else:
        print("❌ ElevenLabs API Key: NOT FOUND")
    
    # Check Supabase URL
    supabase_url = os.getenv('REACT_APP_SUPABASE_URL')
    if supabase_url:
        print(f"✅ Supabase URL: {supabase_url}")
    else:
        print("❌ Supabase URL: NOT FOUND")
    
    # Check Supabase Key
    supabase_key = os.getenv('REACT_APP_SUPABASE_ANON_KEY')
    if supabase_key:
        print(f"✅ Supabase Key: {supabase_key[:8]}...{supabase_key[-4:]}")
    else:
        print("❌ Supabase Key: NOT FOUND")
    
    print()

def test_openai_direct():
    """Test OpenAI API directly"""
    print("=== OPENAI DIRECT TEST ===")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
        if not api_key:
            print("❌ No OpenAI API key found")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test simple completion
        print("Testing simple completion...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenAI!' and nothing else."}
            ],
            max_tokens=10,
            timeout=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI Response: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Direct Test Failed: {e}")
        return False

def test_openai_service():
    """Test our OpenAI service"""
    print("=== OPENAI SERVICE TEST ===")
    
    try:
        from services.openai_service import OpenAIService
        
        service = OpenAIService()
        print(f"✅ OpenAI Service Initialized")
        print(f"   Available: {service.is_available()}")
        print(f"   Model: {service.model}")
        
        # Get status
        status = service.get_status()
        print(f"   Status: {status}")
        
        if service.is_available():
            # Test roleplay flow
            print("Testing roleplay flow...")
            test_result = service.test_roleplay_flow()
            print(f"   Flow Test: {test_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Service Test Failed: {e}")
        return False

def test_roleplay_engine():
    """Test roleplay engine"""
    print("=== ROLEPLAY ENGINE TEST ===")
    
    try:
        from services.roleplay_engine import RoleplayEngine
        
        engine = RoleplayEngine()
        print(f"✅ Roleplay Engine Initialized")
        
        # Get status
        status = engine.get_service_status()
        print(f"   Status: {status}")
        
        # Test session creation
        print("Testing session creation...")
        user_context = {
            'first_name': 'Test',
            'prospect_job_title': 'CTO',
            'prospect_industry': 'Technology'
        }
        
        session_result = engine.create_session(
            user_id='test_user',
            roleplay_id=1,
            mode='practice',
            user_context=user_context
        )
        
        if session_result.get('success'):
            session_id = session_result['session_id']
            print(f"✅ Session Created: {session_id}")
            print(f"   Initial Response: {session_result.get('initial_response')}")
            
            # Test user input processing
            print("Testing user input processing...")
            response_result = engine.process_user_input(
                session_id,
                "Hi, I know this is out of the blue, but can I tell you why I'm calling?"
            )
            
            if response_result.get('success'):
                print(f"✅ Input Processed Successfully")
                print(f"   AI Response: {response_result.get('ai_response')}")
                print(f"   Evaluation: {response_result.get('evaluation')}")
                print(f"   Call Continues: {response_result.get('call_continues')}")
            else:
                print(f"❌ Input Processing Failed: {response_result.get('error')}")
            
            # Test session ending
            print("Testing session ending...")
            end_result = engine.end_session(session_id)
            
            if end_result.get('success'):
                print(f"✅ Session Ended Successfully")
                print(f"   Score: {end_result.get('overall_score')}")
                print(f"   Coaching: {end_result.get('coaching')}")
            else:
                print(f"❌ Session Ending Failed: {end_result.get('error')}")
        
        else:
            print(f"❌ Session Creation Failed: {session_result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Roleplay Engine Test Failed: {e}")
        return False

def test_elevenlabs_service():
    """Test ElevenLabs service"""
    print("=== ELEVENLABS SERVICE TEST ===")
    
    try:
        from services.elevenlabs_service import ElevenLabsService
        
        service = ElevenLabsService()
        print(f"✅ ElevenLabs Service Initialized")
        print(f"   Available: {service.is_available()}")
        
        if hasattr(service, 'get_status'):
            status = service.get_status()
            print(f"   Status: {status}")
        
        if service.is_available():
            # Test TTS
            print("Testing TTS generation...")
            try:
                audio_stream = service.text_to_speech("Hello, this is a test.")
                if audio_stream:
                    audio_data = audio_stream.getvalue()
                    print(f"✅ TTS Generated: {len(audio_data)} bytes")
                else:
                    print("❌ TTS returned None")
            except Exception as e:
                print(f"❌ TTS Generation Failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ElevenLabs Service Test Failed: {e}")
        return False

def test_full_conversation():
    """Test a full conversation flow"""
    print("=== FULL CONVERSATION TEST ===")
    
    try:
        from services.roleplay_engine import RoleplayEngine
        
        engine = RoleplayEngine()
        
        # Create session
        user_context = {
            'first_name': 'Test',
            'prospect_job_title': 'CTO',
            'prospect_industry': 'Technology'
        }
        
        session_result = engine.create_session(
            user_id='test_user_full',
            roleplay_id=1,
            mode='practice',
            user_context=user_context
        )
        
        if not session_result.get('success'):
            print(f"❌ Session creation failed: {session_result.get('error')}")
            return False
        
        session_id = session_result['session_id']
        print(f"✅ Session Created: {session_id}")
        print(f"Prospect: {session_result.get('initial_response')}")
        
        # Simulate a conversation
        conversation_steps = [
            "Hi, I know this is out of the blue, but can I tell you why I'm calling?",
            "Fair enough. I work with CTOs like yourself who are struggling with data silos. Can I ask you a quick question?",
            "We help companies like yours connect their data sources in minutes instead of months. How are you currently handling data integration?",
            "That's exactly what I thought. Would you be open to a 15-minute call next Tuesday at 2 PM to see how this could help?"
        ]
        
        for i, user_input in enumerate(conversation_steps, 1):
            print(f"\n--- Step {i} ---")
            print(f"SDR: {user_input}")
            
            response_result = engine.process_user_input(session_id, user_input)
            
            if response_result.get('success'):
                print(f"Prospect: {response_result.get('ai_response')}")
                print(f"Evaluation: Score={response_result.get('evaluation', {}).get('score', 'N/A')}, "
                      f"Passed={response_result.get('evaluation', {}).get('passed', 'N/A')}")
                
                if not response_result.get('call_continues'):
                    print("Call ended by prospect.")
                    break
            else:
                print(f"❌ Error: {response_result.get('error')}")
                break
        
        # End session
        end_result = engine.end_session(session_id)
        if end_result.get('success'):
            print(f"\n✅ Conversation Complete!")
            print(f"Final Score: {end_result.get('overall_score')}/100")
            print(f"Session Success: {end_result.get('session_success')}")
            print(f"Duration: {end_result.get('duration_minutes')} minutes")
            
            coaching = end_result.get('coaching', {})
            if coaching:
                print(f"\nCoaching Feedback:")
                for category, feedback in coaching.items():
                    print(f"  {category}: {feedback}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full Conversation Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 ROLEPLAY 1.1 SYSTEM TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment loaded")
    except ImportError:
        print("❌ python-dotenv not installed")
    except Exception as e:
        print(f"❌ Environment load error: {e}")
    
    print()
    
    # Run tests
    tests = [
        ("Environment", test_environment),
        ("OpenAI Direct", test_openai_direct),
        ("OpenAI Service", test_openai_service),
        ("Roleplay Engine", test_roleplay_engine),
        ("ElevenLabs Service", test_elevenlabs_service),
        ("Full Conversation", test_full_conversation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Roleplay 1.1 system is ready!")
    else:
        print("🔧 Some tests failed. Check the errors above.")
        
        # Provide guidance
        print("\n💡 TROUBLESHOOTING TIPS:")
        
        if not results.get("Environment"):
            print("- Check your .env file has the correct API keys")
            print("- Make sure REACT_APP_OPENAI_API_KEY is set correctly")
        
        if not results.get("OpenAI Direct"):
            print("- Verify your OpenAI API key is valid and has credits")
            print("- Check your internet connection")
            print("- Try a different model (gpt-3.5-turbo instead of gpt-4o-mini)")
        
        if not results.get("OpenAI Service"):
            print("- Check the services/openai_service.py file")
            print("- Make sure the OpenAI library is installed: pip install openai")
        
        if not results.get("Roleplay Engine"):
            print("- Check the services/roleplay_engine.py file")
            print("- Ensure the OpenAI service is working first")

if __name__ == "__main__":
    main()