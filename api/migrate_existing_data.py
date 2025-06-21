# ===== migrate_existing_data.py =====
# Script to migrate existing voice_sessions to new roleplay_completions table

from services.supabase_client import SupabaseService
from datetime import datetime, timezone
import uuid

def migrate_voice_sessions_to_completions():
    """Migrate existing voice_sessions to new roleplay_completions table"""
    
    supabase_service = SupabaseService()
    client = supabase_service.get_service_client()
    
    print("🔄 Starting migration of voice_sessions to roleplay_completions...")
    
    try:
        # Get all existing voice sessions
        sessions_result = client.table('voice_sessions').select('*').execute()
        
        if not sessions_result.data:
            print("📭 No voice sessions found to migrate")
            return
        
        migrated_count = 0
        
        for session in sessions_result.data:
            try:
                # Create completion record from voice session
                completion_data = {
                    'user_id': session['user_id'],
                    'roleplay_id': str(session['roleplay_id']),  # Convert to string
                    'session_id': session.get('id', str(uuid.uuid4())),
                    'mode': 'practice',  # Default mode for migrated sessions
                    'score': session.get('score', 0),
                    'success': session.get('score', 0) >= 70,  # Consider 70+ as success
                    'duration_minutes': session.get('duration_minutes', 0),
                    'started_at': session.get('created_at', datetime.now(timezone.utc).isoformat()),
                    'completed_at': session.get('ended_at', session.get('created_at', datetime.now(timezone.utc).isoformat())),
                    'conversation_data': session.get('conversation_data', {}),
                    'coaching_feedback': session.get('coaching_feedback', {}),
                    'ai_evaluation': session.get('ai_evaluation'),
                    'rubric_scores': session.get('rubric_scores', {}),
                    'forced_end': session.get('forced_end', False),
                    'migrated_from_voice_session': True  # Mark as migrated
                }
                
                # Insert into roleplay_completions
                result = client.table('roleplay_completions').insert(completion_data).execute()
                
                if result.data:
                    migrated_count += 1
                    print(f"✅ Migrated session {session.get('id', 'unknown')} for user {session['user_id']}")
                else:
                    print(f"❌ Failed to migrate session {session.get('id', 'unknown')}")
                    
            except Exception as e:
                print(f"❌ Error migrating session {session.get('id', 'unknown')}: {e}")
                continue
        
        print(f"\n🎉 Migration completed: {migrated_count}/{len(sessions_result.data)} sessions migrated")
        
        # Update user stats based on migrated data
        print("\n🔄 Updating user stats...")
        update_user_stats_from_completions()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

def update_user_stats_from_completions():
    """Update user_roleplay_stats table based on roleplay_completions"""
    
    supabase_service = SupabaseService()
    client = supabase_service.get_service_client()
    
    try:
        # Get all unique user-roleplay combinations
        completions = client.table('roleplay_completions').select(
            'user_id, roleplay_id, score, completed_at'
        ).execute()
        
        # Group by user and roleplay
        user_stats = {}
        
        for completion in completions.data:
            user_id = completion['user_id']
            roleplay_id = completion['roleplay_id']
            key = f"{user_id}_{roleplay_id}"
            
            if key not in user_stats:
                user_stats[key] = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 0,
                    'best_score': 0,
                    'scores': [],
                    'completed_dates': []
                }
            
            user_stats[key]['total_attempts'] += 1
            user_stats[key]['scores'].append(completion['score'])
            user_stats[key]['completed_dates'].append(completion['completed_at'])
            
            if completion['score'] > user_stats[key]['best_score']:
                user_stats[key]['best_score'] = completion['score']
        
        # Insert/update user_roleplay_stats
        for stats in user_stats.values():
            # Check if record exists
            existing = client.table('user_roleplay_stats').select('*').eq(
                'user_id', stats['user_id']
            ).eq('roleplay_id', stats['roleplay_id']).execute()
            
            stats_data = {
                'user_id': stats['user_id'],
                'roleplay_id': stats['roleplay_id'],
                'total_attempts': stats['total_attempts'],
                'best_score': stats['best_score'],
                'last_score': stats['scores'][-1],
                'completed': stats['best_score'] >= 70,
                'last_attempt_at': max(stats['completed_dates']),
                'best_score_at': stats['completed_dates'][stats['scores'].index(stats['best_score'])],
                'completed_at': max(stats['completed_dates']) if stats['best_score'] >= 70 else None
            }
            
            if existing.data:
                # Update existing
                client.table('user_roleplay_stats').update(stats_data).eq(
                    'user_id', stats['user_id']
                ).eq('roleplay_id', stats['roleplay_id']).execute()
            else:
                # Insert new
                client.table('user_roleplay_stats').insert(stats_data).execute()
        
        print(f"✅ Updated stats for {len(user_stats)} user-roleplay combinations")
        
    except Exception as e:
        print(f"❌ Error updating user stats: {e}")

if __name__ == "__main__":
    print("🚀 Voice Session Migration Script")
    print("=" * 40)
    
    # Confirm before running
    confirm = input("This will migrate existing voice_sessions to the new system. Continue? (y/n): ")
    
    if confirm.lower() == 'y':
        migrate_voice_sessions_to_completions()
    else:
        print("Migration cancelled")