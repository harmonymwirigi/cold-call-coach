# ===== Test Script - Add this to a new file: test_data_flow.py =====

"""
Test script to verify user progress data flow
Run this from your backend to test the data flow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.supabase_client import SupabaseService
from services.user_progress_service import UserProgressService
from datetime import datetime, timezone, timedelta
import json

def test_user_progress_flow(user_id):
    """Test the complete user progress data flow"""
    
    print(f"🧪 Testing user progress flow for user: {user_id}")
    print("=" * 60)
    
    # Initialize services
    supabase = SupabaseService()
    progress_service = UserProgressService()
    
    # Step 1: Check current progress data
    print("\n1️⃣ CURRENT PROGRESS DATA:")
    try:
        current_progress = progress_service.get_user_roleplay_progress(user_id)
        print(f"   Found progress for: {list(current_progress.keys())}")
        
        if '1.2' in current_progress:
            marathon_data = current_progress['1.2']
            print(f"   Marathon Data:")
            print(f"     - Best Run: {marathon_data.get('marathon_best_run', 0)}")
            print(f"     - Marathon Passed: {marathon_data.get('marathon_passed', False)}")
            print(f"     - Total Attempts: {marathon_data.get('total_attempts', 0)}")
            print(f"     - Best Score: {marathon_data.get('best_score', 0)}")
        else:
            print("   ❌ No Marathon (1.2) progress found")
            
    except Exception as e:
        print(f"   ❌ Error getting current progress: {e}")
    
    # Step 2: Check completions table
    print("\n2️⃣ COMPLETIONS TABLE DATA:")
    try:
        client = supabase.get_service_client()
        completions = client.table('roleplay_completions').select('*').eq('user_id', user_id).eq('roleplay_id', '1.2').order('completed_at', desc=True).limit(5).execute()
        
        if completions.data:
            print(f"   Found {len(completions.data)} marathon completions:")
            for i, comp in enumerate(completions.data):
                print(f"     {i+1}. Score: {comp.get('score')}, Success: {comp.get('success')}, Marathon Results: {comp.get('marathon_results')}")
        else:
            print("   ❌ No marathon completions found")
            
    except Exception as e:
        print(f"   ❌ Error getting completions: {e}")
    
    # Step 3: Simulate a successful marathon
    print("\n3️⃣ SIMULATING SUCCESSFUL MARATHON:")
    try:
        completion_data = {
            'user_id': user_id,
            'session_id': f'test_session_{int(datetime.now().timestamp())}',
            'roleplay_id': '1.2',
            'mode': 'marathon',
            'score': 80,
            'success': True,
            'duration_minutes': 30,
            'started_at': (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'marathon_results': {
                'calls_passed': 7,
                'calls_total': 10,
                'marathon_passed': True,
                'marathon_completed': True
            },
            'conversation_data': {'test': 'data'},
            'coaching_feedback': {'test': 'feedback'}
        }
        
        print("   Saving completion...")
        completion_id = progress_service.save_roleplay_completion(completion_data)
        print(f"   ✅ Completion saved with ID: {completion_id}")
        
        print("   Updating progress...")
        progress_updated = progress_service.update_user_progress_after_completion(completion_data)
        print(f"   ✅ Progress updated: {progress_updated}")
        
    except Exception as e:
        print(f"   ❌ Error in simulation: {e}")
    
    # Step 4: Check updated progress
    print("\n4️⃣ UPDATED PROGRESS DATA:")
    try:
        updated_progress = progress_service.get_user_roleplay_progress(user_id, ['1.2'])
        
        if '1.2' in updated_progress:
            marathon_data = updated_progress['1.2']
            print(f"   Marathon Data After Update:")
            print(f"     - Best Run: {marathon_data.get('marathon_best_run', 0)}")
            print(f"     - Marathon Passed: {marathon_data.get('marathon_passed', False)}")
            print(f"     - Total Attempts: {marathon_data.get('total_attempts', 0)}")
            print(f"     - Best Score: {marathon_data.get('best_score', 0)}")
            print(f"     - Passed Flag: {marathon_data.get('passed', False)}")
        else:
            print("   ❌ Still no Marathon progress found!")
            
    except Exception as e:
        print(f"   ❌ Error getting updated progress: {e}")
    
    # Step 5: Check access to advanced roleplays
    print("\n5️⃣ ACCESS CHECKS:")
    for roleplay_id in ['1.3', '2.1']:
        try:
            access_check = progress_service.check_roleplay_access(user_id, roleplay_id)
            print(f"   {roleplay_id}: {'✅ ALLOWED' if access_check['allowed'] else '❌ DENIED'} - {access_check['reason']}")
        except Exception as e:
            print(f"   {roleplay_id}: ❌ Error checking access: {e}")
    
    # Step 6: Test what the frontend would receive
    print("\n6️⃣ FRONTEND SIMULATION:")
    try:
        # This simulates what the roleplay/1 route would pass to the template
        user_progress = progress_service.get_user_roleplay_progress(user_id, ['1.1', '1.2', '1.3'])
        
        print(f"   Frontend would receive progress for: {list(user_progress.keys())}")
        print(f"   Marathon data would be: {json.dumps(user_progress.get('1.2', {}), indent=4)}")
        
    except Exception as e:
        print(f"   ❌ Error in frontend simulation: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    
    return True

def fix_marathon_manually(user_id, calls_passed=6):
    """Manually fix marathon data for a user"""
    print(f"🔧 Manually fixing marathon data for user {user_id}")
    
    try:
        supabase = SupabaseService()
        client = supabase.get_service_client()
        
        # Get or create progress record
        existing = client.table('user_roleplay_progress').select('*').eq(
            'user_id', user_id
        ).eq('roleplay_id', '1.2').execute()
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing.data:
            # Update existing
            current = existing.data[0]
            updates = {
                'marathon_best_run': max(current.get('marathon_best_run', 0), calls_passed),
                'marathon_completed': True,
                'marathon_passed': calls_passed >= 6,
                'best_score': max(current.get('best_score', 0), 75),
                'total_attempts': current.get('total_attempts', 0) + 1,
                'successful_attempts': current.get('successful_attempts', 0) + 1,
                'updated_at': now
            }
            
            result = client.table('user_roleplay_progress').update(updates).eq('id', current['id']).execute()
            print(f"✅ Updated existing record: {updates}")
            
        else:
            # Create new
            new_record = {
                'user_id': user_id,
                'roleplay_id': '1.2',
                'marathon_best_run': calls_passed,
                'marathon_completed': True,
                'marathon_passed': calls_passed >= 6,
                'best_score': 75,
                'total_attempts': 1,
                'successful_attempts': 1,
                'is_unlocked': True,
                'first_attempt_at': now,
                'last_attempt_at': now,
                'created_at': now
            }
            
            result = client.table('user_roleplay_progress').insert(new_record).execute()
            print(f"✅ Created new record: {new_record}")
        
        print("✅ Marathon data fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing marathon data: {e}")
        return False

if __name__ == "__main__":
    # Replace with an actual user ID from your database
    test_user_id = "your-test-user-id-here"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_user_progress_flow(test_user_id)
        elif sys.argv[1] == "fix":
            fix_marathon_manually(test_user_id, 6)
    else:
        print("Usage:")
        print("  python test_data_flow.py test   # Run full test")
        print("  python test_data_flow.py fix    # Fix marathon data manually")