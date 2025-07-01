# ===== FIXED: api/routes/roleplay.py - Session Management =====

from flask import Blueprint, request, jsonify, session, Response, redirect, render_template, url_for
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Import services with error handling
try:
    from services.supabase_client import SupabaseService
    from services.elevenlabs_service import ElevenLabsService  
    from services.roleplay_engine import RoleplayEngine
    from services.user_progress_service import UserProgressService 
except ImportError as e:
    logger.error(f"Service import error: {e}")

# Import utilities with error handling  
try:
    from utils.decorators import require_auth, check_usage_limits, validate_json_input, log_api_call
    from utils.helpers import log_user_action, format_duration
    from utils.constants import ROLEPLAY_CONFIG
except ImportError as e:
    logger.error(f"Utils import error: {e}")

# Create blueprint
roleplay_bp = Blueprint('roleplay', __name__, url_prefix='/api/roleplay')

# Initialize services
try:
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()
    progress_service = UserProgressService()
    logger.info("✅ Roleplay services initialized successfully")
except Exception as e:
    logger.error(f"❌ Error initializing services: {e}")
    supabase_service = None
    elevenlabs_service = None
    roleplay_engine = None
    progress_service = None

# ===== ENHANCED SESSION STORAGE =====
session_storage = {}  # In-memory backup
DATABASE_SESSION_STORAGE = True

def store_session_reliably(session_id: str, user_id: str, session_data: Dict) -> bool:
    """Enhanced session storage with multiple fallbacks"""
    try:
        # Store in Flask session
        session['current_roleplay_session'] = session_id
        session['roleplay_user_id'] = user_id
        session['session_data'] = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': session_data.get('roleplay_id'),
            'started_at': session_data.get('started_at'),
            'current_stage': session_data.get('current_stage', 'phone_pickup'),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        
        # Store in memory backup (CRITICAL for marathon mode)
        session_storage[session_id] = {
            'user_id': user_id,
            'session_data': session_data,
            'stored_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        
        # Also store a user-to-session mapping for quick lookup
        user_session_key = f"user_{user_id}_current_session"
        session_storage[user_session_key] = session_id
        
        # Store in database for persistence (if available)
        if DATABASE_SESSION_STORAGE and supabase_service:
            try:
                supabase_service.upsert_data('active_roleplay_sessions', {
                    'session_id': session_id,
                    'user_id': user_id,
                    'session_data': session_data,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'last_activity': datetime.now(timezone.utc).isoformat(),
                    'is_active': True
                })
                logger.info(f"Session {session_id} stored in database")
            except Exception as db_error:
                logger.warning(f"Failed to store session in database: {db_error}")
        
        logger.info(f"Session {session_id} stored reliably for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store session reliably: {e}")
        return False
def retrieve_session_reliably(session_id: str, user_id: str) -> Optional[Dict]:
    """Enhanced session retrieval with multiple fallbacks"""
    try:
        # 1. Check roleplay engine's active memory first
        if roleplay_engine and session_id in roleplay_engine.active_sessions:
            session_data = roleplay_engine.active_sessions[session_id]
            if session_data.get('user_id') == user_id:
                logger.info(f"Session {session_id} found in roleplay engine memory")
                # Update activity timestamp
                update_session_activity(session_id)
                return session_data

        # 2. Check in-memory backup
        if session_id in session_storage:
            stored_session = session_storage[session_id]
            if stored_session.get('user_id') == user_id:
                session_data = stored_session['session_data']
                logger.info(f"Session {session_id} recovered from memory backup")
                
                # Restore to roleplay engine
                if roleplay_engine:
                    roleplay_engine.active_sessions[session_id] = session_data
                
                update_session_activity(session_id)
                return session_data

        # 3. Try to find by user ID if session_id lookup failed
        user_session_key = f"user_{user_id}_current_session"
        if user_session_key in session_storage:
            actual_session_id = session_storage[user_session_key]
            if actual_session_id != session_id:
                logger.info(f"Found different session for user {user_id}: {actual_session_id}")
                return retrieve_session_reliably(actual_session_id, user_id)

        # 4. Check Flask session
        flask_session_id = session.get('current_roleplay_session')
        if flask_session_id and flask_session_id != session_id:
            logger.info(f"Flask session has different session ID: {flask_session_id}")
            return retrieve_session_reliably(flask_session_id, user_id)

        # 5. Database recovery as last resort
        if DATABASE_SESSION_STORAGE and supabase_service:
            logger.warning(f"Session {session_id} not in memory. Attempting DB recovery...")
            records = supabase_service.get_data_with_filter(
                'active_roleplay_sessions', 'session_id', session_id,
                additional_filters={'user_id': user_id, 'is_active': True}
            )
            if records:
                session_data = records[0].get('session_data')
                if session_data:
                    logger.info(f"Session {session_id} successfully recovered from database")
                    # Restore to both memory stores
                    if roleplay_engine:
                        roleplay_engine.active_sessions[session_id] = session_data
                    session_storage[session_id] = {
                        'user_id': user_id,
                        'session_data': session_data,
                        'stored_at': datetime.now(timezone.utc).isoformat(),
                        'last_activity': datetime.now(timezone.utc).isoformat()
                    }
                    return session_data

        logger.error(f"SESSION RECOVERY FAILED for user {user_id} and session {session_id}")
        return None
        
    except Exception as e:
        logger.error(f"Critical error during session retrieval for {session_id}: {e}", exc_info=True)
        return None

def update_session_activity(session_id: str) -> None:
    """Update session last activity timestamp in all stores"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Update in memory
        if session_id in session_storage:
            session_storage[session_id]['last_activity'] = timestamp
        
        # Update in database
        if DATABASE_SESSION_STORAGE and supabase_service:
            try:
                supabase_service.update_data_by_id(
                    'active_roleplay_sessions',
                    {'session_id': session_id},
                    {'last_activity': timestamp}
                )
            except Exception as db_error:
                logger.warning(f"Failed to update session activity in DB: {db_error}")
                
    except Exception as e:
        logger.warning(f"Failed to update session activity: {e}")
def cleanup_session(session_id: str) -> None:
    """Enhanced session cleanup"""
    try:
        # Remove from memory stores
        session_storage.pop(session_id, None)
        
        # Remove user-to-session mapping
        for key in list(session_storage.keys()):
            if key.startswith('user_') and key.endswith('_current_session'):
                if session_storage[key] == session_id:
                    session_storage.pop(key, None)
        
        # Remove from database
        if DATABASE_SESSION_STORAGE and supabase_service:
            try:
                supabase_service.update_data_by_id(
                    'active_roleplay_sessions',
                    {'session_id': session_id},
                    {'is_active': False, 'ended_at': datetime.now(timezone.utc).isoformat()}
                )
            except Exception as db_error:
                logger.warning(f"Failed to cleanup session in database: {db_error}")
        
        # Clear from Flask session if it matches
        if session.get('current_roleplay_session') == session_id:
            session.pop('current_roleplay_session', None)
            session.pop('roleplay_user_id', None)
            session.pop('session_data', None)
        
        logger.info(f"Session {session_id} cleaned up")
        
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")

@roleplay_bp.route('/session/debug', methods=['GET'])
def debug_session_info():
    """Debug endpoint to check session status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        flask_session_id = session.get('current_roleplay_session')
        user_session_key = f"user_{user_id}_current_session"
        memory_session_id = session_storage.get(user_session_key)
        
        engine_sessions = []
        if roleplay_engine:
            for sid, sdata in roleplay_engine.active_sessions.items():
                if sdata.get('user_id') == user_id:
                    engine_sessions.append({
                        'session_id': sid,
                        'active': sdata.get('session_active', False),
                        'stage': sdata.get('current_stage', 'unknown'),
                        'turn_count': sdata.get('turn_count', 0)
                    })
        
        return jsonify({
            'user_id': user_id,
            'flask_session_id': flask_session_id,
            'memory_session_id': memory_session_id,
            'engine_sessions': engine_sessions,
            'memory_store_keys': list(session_storage.keys()),
            'session_storage_count': len([k for k in session_storage.keys() if not k.startswith('user_')])
        })
        
    except Exception as e:
        logger.error(f"Debug session error: {e}")
        return jsonify({'error': str(e)}), 500

@roleplay_bp.route('/start', methods=['POST'])
def start_roleplay():
    """ENHANCED: Start roleplay session with robust session management"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        roleplay_id = data.get('roleplay_id')
        mode = data.get('mode', 'practice')
        
        logger.info(f"🚀 Starting roleplay: {roleplay_id}, mode={mode}, user={user_id}")
        
        # Check if roleplay engine is available
        if not roleplay_engine:
            logger.error("❌ Roleplay engine not available")
            return jsonify({'error': 'Roleplay service unavailable'}), 503
        
        # Clean up any existing sessions for this user more thoroughly
        existing_session_id = session.get('current_roleplay_session')
        user_session_key = f"user_{user_id}_current_session"
        
        # Check memory for existing sessions
        if user_session_key in session_storage:
            old_session_id = session_storage[user_session_key]
            logger.info(f"🧹 Found existing session in memory: {old_session_id}")
            try:
                roleplay_engine.end_session(old_session_id, forced_end=True)
                cleanup_session(old_session_id)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up memory session: {cleanup_error}")
        
        # Clean up Flask session if different
        if existing_session_id and existing_session_id != session_storage.get(user_session_key):
            logger.info(f"🧹 Cleaning up Flask session: {existing_session_id}")
            try:
                roleplay_engine.end_session(existing_session_id, forced_end=True)
                cleanup_session(existing_session_id)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up Flask session: {cleanup_error}")
        
        # Get user profile and context
        try:
            if supabase_service:
                profile = supabase_service.get_user_profile_by_service(user_id)
            else:
                profile = None
        except Exception as profile_error:
            logger.warning(f"Failed to get user profile: {profile_error}")
            profile = None
            
        if not profile:
            profile = {
                'first_name': 'User',
                'prospect_job_title': 'CTO',
                'prospect_industry': 'Technology'
            }
        
        user_context = {
            'first_name': profile.get('first_name', 'User'),
            'prospect_job_title': profile.get('prospect_job_title', 'CTO'),
            'prospect_industry': profile.get('prospect_industry', 'Technology'),
            'access_level': profile.get('access_level', 'limited_trial'),
            'roleplay_version': roleplay_id
        }
        
        # Create roleplay session
        try:
            logger.info(f"📞 Creating roleplay session: {roleplay_id}")
            session_result = roleplay_engine.create_session(
                user_id=user_id,
                roleplay_id=roleplay_id,
                mode=mode,
                user_context=user_context
            )
            logger.info(f"📞 Session creation result: {session_result.get('success', False)}")
        except Exception as engine_error:
            logger.error(f"❌ Roleplay engine error: {engine_error}")
            return jsonify({'error': f'Failed to create session: {str(engine_error)}'}), 500
        
        if not session_result.get('success'):
            error_msg = session_result.get('error', 'Failed to create session')
            logger.error(f"❌ Session creation failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        session_id = session_result['session_id']
        logger.info(f"✅ Session created successfully: {session_id}")
        
        # Store session reliably with enhanced storage
        session_data = roleplay_engine.active_sessions.get(session_id, {})
        success = store_session_reliably(session_id, user_id, session_data)
        
        if not success:
            logger.error("❌ Failed to store session reliably")
            return jsonify({'error': 'Failed to initialize session storage'}), 500
        
        # Prepare response data
        response_data = {
            'message': f'Roleplay {roleplay_id} session started successfully',
            'session_id': session_id,
            'roleplay_id': roleplay_id,
            'mode': mode,
            'initial_response': session_result.get('initial_response', 'Hello?'),
            'roleplay_info': session_result.get('roleplay_info', {}),
            'tts_available': elevenlabs_service.is_available() if elevenlabs_service and hasattr(elevenlabs_service, 'is_available') else False,
            'session_stored': True,
            'user_context': user_context,
            'marathon_status': session_result.get('marathon_status', None)  # Include marathon status
        }
        
        logger.info(f"✅ Roleplay {roleplay_id} session started successfully: {session_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Critical error starting roleplay: {e}")
        return jsonify({'error': 'Internal server error during session creation'}), 500
@roleplay_bp.route('/respond', methods=['POST'])
def handle_user_response():
    """ENHANCED: Handle user input with robust session recovery"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        user_id = session.get('user_id')
        
        if not user_id: 
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Enhanced session recovery
        session_id_from_cookie = session.get('current_roleplay_session')
        
        # Try multiple ways to find the session
        session_data = None
        actual_session_id = None
        
        # 1. Try with the cookie session ID
        if session_id_from_cookie:
            session_data = retrieve_session_reliably(session_id_from_cookie, user_id)
            if session_data:
                actual_session_id = session_id_from_cookie
        
        # 2. Try to find user's current session if cookie failed
        if not session_data:
            user_session_key = f"user_{user_id}_current_session"
            if user_session_key in session_storage:
                potential_session_id = session_storage[user_session_key]
                session_data = retrieve_session_reliably(potential_session_id, user_id)
                if session_data:
                    actual_session_id = potential_session_id
                    # Update Flask session
                    session['current_roleplay_session'] = actual_session_id
        
        # 3. Check if roleplay engine has any sessions for this user
        if not session_data and roleplay_engine:
            for sid, sdata in roleplay_engine.active_sessions.items():
                if sdata.get('user_id') == user_id and sdata.get('session_active', False):
                    session_data = sdata
                    actual_session_id = sid
                    # Update both session stores
                    session['current_roleplay_session'] = actual_session_id
                    session_storage[f"user_{user_id}_current_session"] = actual_session_id
                    logger.info(f"Found session in roleplay engine: {actual_session_id}")
                    break
        
        if not session_data or not actual_session_id:
            logger.error(f"No session found for user {user_id}. Cookie session: {session_id_from_cookie}")
            return jsonify({
                'error': 'No active roleplay session found. Please start a new call.',
                'session_expired': True, 
                'action_required': 'restart_call'
            }), 404

        logger.info(f"💬 Processing input for session {actual_session_id}: '{user_input[:50]}...'")
        
        # Update activity timestamp
        update_session_activity(actual_session_id)
        
        # Process input with the correct session ID
        response_result = roleplay_engine.process_user_input(actual_session_id, user_input)
        
        # Store updated session data
        updated_session_data = roleplay_engine.active_sessions.get(actual_session_id)
        if updated_session_data:
            store_session_reliably(actual_session_id, user_id, updated_session_data)

        return jsonify(response_result)
        
    except Exception as e:
        logger.error(f"❌ Critical error handling user response: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'action_required': 'restart_call'}), 500
# Keep all other existing endpoints...
@roleplay_bp.route('/end', methods=['POST'])
def end_roleplay():
    """End roleplay session with comprehensive cleanup"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        forced_end = data.get('forced_end', False)
        session_id = session.get('current_roleplay_session')
        
        # Try to find session if not in Flask session
        if not session_id:
            user_session_key = f"user_{user_id}_current_session"
            session_id = session_storage.get(user_session_key)
        
        if not session_id:
            logger.warning("⚠️ No active session to end")
            return jsonify({'message': 'No active session found'}), 200
        
        logger.info(f"📞 Ending roleplay session {session_id} for user {user_id}")
        
        # Check if roleplay engine is available
        if not roleplay_engine:
            logger.error("❌ Roleplay engine not available for session end")
            cleanup_session(session_id)
            return jsonify({
                'message': 'Session ended (service unavailable)',
                'overall_score': 50,
                'coaching': {'error': 'Service unavailable'},
                'session_cleaned': True
            })
        
        # End session through engine
        try:
            end_result = roleplay_engine.end_session(session_id, forced_end)
        except Exception as engine_error:
            logger.error(f"❌ Roleplay engine end error: {engine_error}")
            end_result = {
                'success': True,
                'duration_minutes': 1,
                'session_success': False,
                'coaching': {'error': 'Session ended with errors'},
                'overall_score': 50
            }
        
        # Clean up session completely
        cleanup_session(session_id)
        
        # Prepare response
        response_data = {
            'message': 'Roleplay session ended successfully',
            'duration_minutes': end_result.get('duration_minutes', 1),
            'session_success': end_result.get('session_success', False),
            'coaching': end_result.get('coaching', {}),
            'overall_score': end_result.get('overall_score', 50),
            'completion_message': f"Session complete! Score: {end_result.get('overall_score', 50)}/100",
            'roleplay_type': end_result.get('roleplay_type', 'practice'),
            'marathon_results': end_result.get('marathon_results', None),
            'session_cleaned': True
        }
        
        logger.info(f"✅ Roleplay session ended successfully. Score: {end_result.get('overall_score', 50)}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Critical error ending roleplay: {e}")
        
        # Emergency cleanup
        try:
            session_id = session.get('current_roleplay_session')
            if session_id:
                cleanup_session(session_id)
        except Exception as cleanup_error:
            logger.error(f"❌ Emergency cleanup failed: {cleanup_error}")
        
        return jsonify({
            'error': 'Internal server error during session end',
            'message': 'Session has been cleaned up',
            'technical_details': str(e)
        }), 500


@roleplay_bp.route('/info/<roleplay_id>', methods=['GET'])
def get_roleplay_info(roleplay_id):
    """Get roleplay information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # CRITICAL: Check if roleplay engine is available
        if not roleplay_engine:
            logger.error("❌ Roleplay engine not available")
            # Return fallback info
            return jsonify({
                'id': roleplay_id,
                'name': f'Roleplay {roleplay_id}',
                'description': 'Cold calling training',
                'type': 'practice',
                'features': {'ai_evaluation': False, 'basic_coaching': True}
            })
        
        # Get info from engine
        roleplay_info = roleplay_engine.get_roleplay_info(roleplay_id)
        
        if 'error' in roleplay_info:
            return jsonify({'error': f'Invalid roleplay ID: {roleplay_id}'}), 404
        
        logger.info(f"✅ Roleplay info retrieved for {roleplay_id}")
        return jsonify(roleplay_info)
        
    except Exception as e:
        logger.error(f"❌ Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/available', methods=['GET'])
def get_available_roleplays():
    """Get list of available roleplay types"""
    try:
        # CRITICAL: Check if roleplay engine is available
        if not roleplay_engine:
            logger.error("❌ Roleplay engine not available")
            return jsonify({
                'available_roleplays': ['1.1'],
                'roleplay_details': {
                    '1.1': {
                        'id': '1.1',
                        'name': 'Practice Mode',
                        'description': 'Basic cold calling practice',
                        'error': 'Service unavailable'
                    }
                }
            })
        
        available_roleplays = roleplay_engine.get_available_roleplays()
        
        roleplay_details = {}
        for roleplay_id in available_roleplays:
            try:
                roleplay_details[roleplay_id] = roleplay_engine.get_roleplay_info(roleplay_id)
            except Exception as e:
                logger.warning(f"Could not get info for roleplay {roleplay_id}: {e}")
                roleplay_details[roleplay_id] = {
                    'id': roleplay_id,
                    'name': f'Roleplay {roleplay_id}',
                    'description': 'Roleplay training',
                    'error': str(e)
                }
        
        return jsonify({
            'available_roleplays': available_roleplays,
            'roleplay_details': roleplay_details
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting available roleplays: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech for Roleplay"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        logger.info(f"🔊 TTS request from user {user_id}: '{text[:50]}...'")
        
        # Handle empty text
        if not text:
            return _create_silent_audio_response()
        
        # Limit text length
        if len(text) > 2500:
            text = text[:2500]
            logger.warning("Text truncated to 2500 characters for TTS")
        
        # Generate speech (if service available)
        audio_data = None
        try:
            if elevenlabs_service and hasattr(elevenlabs_service, 'text_to_speech'):
                audio_stream = elevenlabs_service.text_to_speech(text)
                if audio_stream:
                    audio_data = audio_stream.getvalue()
                    logger.info(f"✅ TTS generated successfully: {len(audio_data)} bytes")
        except Exception as tts_error:
            logger.warning(f"⚠️ TTS generation failed: {tts_error}")
        
        # Use fallback if needed
        if not audio_data or len(audio_data) < 44:
            logger.info("🔊 Using fallback audio")
            audio_data = _create_emergency_audio_data(text)
        
        # Return audio
        return Response(
            audio_data,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=roleplay_speech.wav',
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'no-cache',
                'Accept-Ranges': 'bytes'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Critical TTS error: {e}")
        return _create_emergency_audio_response()

@roleplay_bp.route('/session/status', methods=['GET'])
def get_session_status():
    """FIXED: Get current session status with recovery"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'active': False, 'session': None})
        
        # Try to retrieve session
        session_data = retrieve_session_reliably(session_id, user_id)
        
        if not session_data:
            session.pop('current_roleplay_session', None)
            return jsonify({'active': False, 'session': None, 'message': 'Session not found'})
        
        response_data = {
            'active': session_data.get('session_active', False),
            'session': {
                'session_id': session_id,
                'current_stage': session_data.get('current_stage', 'unknown'),
                'conversation_length': len(session_data.get('conversation_history', [])),
                'openai_available': roleplay_engine.is_openai_available() if roleplay_engine else False,
                'user_id': session_data.get('user_id'),
                'roleplay_id': session_data.get('roleplay_id'),
                'mode': session_data.get('mode')
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error getting session status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@roleplay_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for Roleplay system"""
    try:
        # Check services
        services_status = {
            'roleplay_engine': 'running' if roleplay_engine else 'unavailable',
            'openai_service': 'available' if roleplay_engine and roleplay_engine.is_openai_available() else 'unavailable',
            'tts_service': 'available' if elevenlabs_service and hasattr(elevenlabs_service, 'is_available') and elevenlabs_service.is_available() else 'unavailable',
            'database': 'connected' if supabase_service else 'unavailable'
        }
        
        status_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.1',
            'services': services_status,
            'active_sessions': len(getattr(roleplay_engine, 'active_sessions', {})) if roleplay_engine else 0
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

# ===== HELPER FUNCTIONS =====

def _create_silent_audio_response():
    """Create silent audio response"""
    try:
        # Minimal WAV header for silence
        silent_audio = (
            b'RIFF\x2a\x00\x00\x00WAVE'
            b'fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00'
            b'data\x02\x00\x00\x00\x00\x00'
        )
        
        return Response(
            silent_audio,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=silence.wav',
                'Content-Length': str(len(silent_audio)),
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        logger.error(f"Error creating silent audio: {e}")
        return Response(b'', mimetype='audio/wav')

def _create_emergency_audio_data(text: str = None) -> bytes:
    """Create emergency audio when everything fails"""
    try:
        # Minimal WAV header
        emergency_audio = (
            b'RIFF\x2a\x00\x00\x00WAVE'
            b'fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00'
            b'data\x02\x00\x00\x00\x00\x00'
        )
        return emergency_audio
    except Exception as e:
        logger.error(f"Error creating emergency audio: {e}")
        return b''

def _create_emergency_audio_response():
    """Create emergency audio response"""
    try:
        emergency_audio = _create_emergency_audio_data()
        return Response(
            emergency_audio,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=emergency.wav',
                'Content-Length': str(len(emergency_audio)),
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        logger.error(f"Emergency audio response failed: {e}")
        return Response(b'', mimetype='audio/wav')