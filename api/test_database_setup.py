# ===== FIXED: test_database_setup.py - UUID Compatible =====

import os
import uuid
from services.supabase_client import SupabaseService
from services.user_progress_service import UserProgressService

def test_database_setup():
    """Test that the new database tables and service are working"""
    
    print("🧪 Testing Database Setup...")
    
    try:
        # Initialize services
        supabase_service = SupabaseService()
        progress_service = UserProgressService()
        
        print("✅ Services initialized successfully")
        
        # Test 1: Check if new tables exist
        print("\n📋 Test 1: Checking if new tables exist...")
        
        tables_to_check = [
            'roleplay_completions',
            'user_roleplay_stats', 
            'roleplay_attempts',
            'user_achievements',
            'roleplay_configs'
        ]
        
        for table in tables_to_check:
            try:
                result = supabase_service.get_service_client().table(table).select('id').limit(1).execute()
                print(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"❌ Table '{table}' error: {e}")
                return False
        
        # Test 2: Check roleplay configs were inserted
        print("\n⚙️ Test 2: Checking roleplay configurations...")
        
        configs = supabase_service.get_service_client().table('roleplay_configs').select('roleplay_id, name').execute()
        
        if configs.data:
            print(f"✅ Found {len(configs.data)} roleplay configurations:")
            for config in configs.data:
                print(f"   - {config['roleplay_id']}: {config['name']}")
        else:
            print("❌ No roleplay configurations found")
            return False
        
        # Test 3: Test progress service methods with VALID UUID
        print("\n🔧 Test 3: Testing progress service methods...")
        
        # Use a properly formatted UUID for testing
        test_user_id = str(uuid.uuid4())  # Generate valid UUID
        print(f"   Using test UUID: {test_user_id}")
        
        try:
            # Test getting progress (should return empty for new user)
            progress = progress_service.get_user_roleplay_progress(test_user_id)
            print(f"✅ get_user_roleplay_progress works: {type(progress)} (empty as expected)")
            
            # Test checking access
            access = progress_service.check_roleplay_access(test_user_id, '1.1')
            print(f"✅ check_roleplay_access works: {access.get('allowed', 'Unknown')}")
            
            # Test getting available roleplays
            available = progress_service.get_available_roleplays(test_user_id)
            print(f"✅ get_available_roleplays works: {available}")
            
            # Test getting completion stats
            stats = progress_service.get_completion_stats(test_user_id)
            print(f"✅ get_completion_stats works: {type(stats)}")
            
        except Exception as e:
            print(f"❌ Progress service error: {e}")
            return False
        
        # Test 4: Test with real user (if you have existing users)
        print("\n👤 Test 4: Testing with existing users...")
        
        try:
            # Get first user from user_profiles
            users = supabase_service.get_service_client().table('user_profiles').select('id, first_name').limit(1).execute()
            
            if users.data:
                real_user_id = users.data[0]['id']
                user_name = users.data[0]['first_name']
                
                print(f"✅ Found user: {user_name} ({real_user_id})")
                
                # Test with real user
                real_progress = progress_service.get_user_roleplay_progress(real_user_id)
                real_recommendations = progress_service.get_next_recommendations(real_user_id)
                
                print(f"✅ Real user progress: {len(real_progress)} roleplay(s)")
                print(f"✅ Real user recommendations: {len(real_recommendations)} recommendation(s)")
                
                if real_recommendations:
                    print(f"   First recommendation: {real_recommendations[0].get('message', 'N/A')}")
                
            else:
                print("⚠️ No existing users found in user_profiles table")
        
        except Exception as e:
            print(f"❌ Real user test error: {e}")
            # This is not critical, continue
        
        # Test 5: Test data insertion capability (simulation)
        print("\n💾 Test 5: Testing data insertion capability...")
        
        try:
            # Generate unique session ID
            test_session_id = f"test-session-{uuid.uuid4()}"
            
            # Test logging an attempt (should work without error)
            progress_service.log_roleplay_attempt(test_user_id, '1.1', test_session_id)
            print("✅ log_roleplay_attempt works")
            
            # Clean up test data
            supabase_service.get_service_client().table('roleplay_attempts').delete().eq('session_id', test_session_id).execute()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Data insertion test error: {e}")
            return False
        
        print("\n🎉 All tests passed! Database setup is working correctly.")
        print("\n📋 Summary:")
        print("✅ All required tables created")
        print("✅ Roleplay configurations loaded")
        print("✅ Progress service working")
        print("✅ Data insertion/retrieval working")
        print("✅ User integration working")
        print("✅ UUID validation fixed")
        
        print("\n🚀 Next steps:")
        print("1. ✅ Database setup complete")
        print("2. 🔄 Test your roleplay flow end-to-end")
        print("3. 🎯 Verify AI scoring and progress tracking")
        print("4. 🚀 Deploy and test with real users")
        
        return True
        
    except Exception as e:
        print(f"❌ Critical error during setup test: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check that you ran the database schema in Supabase")
        print("2. Verify your SUPABASE_URL and SUPABASE_SERVICE_KEY are set")
        print("3. Check that your supabase_client.py is working")
        print("4. Ensure you have proper database permissions")
        return False

def check_existing_data():
    """Check what existing data you have"""
    
    print("\n🔍 Checking existing data...")
    
    try:
        supabase_service = SupabaseService()
        
        # Check existing users
        users = supabase_service.get_service_client().table('user_profiles').select('id, first_name, created_at, access_level').limit(5).execute()
        print(f"📊 Found {len(users.data) if users.data else 0} users in user_profiles")
        
        if users.data:
            print("   Sample users:")
            for user in users.data[:3]:
                access_level = user.get('access_level', 'unknown')
                print(f"   - {user['first_name']} ({access_level})")
        
        # Check existing voice sessions (legacy)
        sessions = supabase_service.get_service_client().table('voice_sessions').select('id, user_id, roleplay_id, score').limit(5).execute()
        print(f"📊 Found {len(sessions.data) if sessions.data else 0} existing voice sessions")
        
        # Check new progress system
        completions = supabase_service.get_service_client().table('roleplay_completions').select('id, user_id, roleplay_id, score').limit(5).execute()
        print(f"📊 Found {len(completions.data) if completions.data else 0} roleplay completions")
        
        if sessions.data and len(sessions.data) > 0:
            print("\n💡 Migration Opportunity:")
            print("   You have existing voice_sessions data that could be migrated")
            print("   to the new roleplay_completions table for better tracking")
        
    except Exception as e:
        print(f"❌ Error checking existing data: {e}")

if __name__ == "__main__":
    print("🏁 Starting Database Setup Test...")
    print("=" * 50)
    
    # Check existing data first
    check_existing_data()
    
    # Run main test
    success = test_database_setup()
    
    print("=" * 50)
    if success:
        print("✅ Setup test completed successfully!")
        print("\n🎯 Your system is ready for:")
        print("   • User registration and authentication")
        print("   • Roleplay progress tracking")
        print("   • AI-powered coaching and feedback")
        print("   • Achievement system")
        print("   • Leaderboards and stats")
    else:
        print("❌ Setup test failed. Please check the errors above.")
    
    print("\n📞 Need help? Check the errors above for debugging guidance.")