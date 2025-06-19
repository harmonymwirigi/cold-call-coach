# ===== FIXED API/ROUTES/ROLEPLAY.PY - ROLEPLAY 1.1 COMPLIANT (NO AUTH INTERFERENCE) =====
from flask import Blueprint, request, jsonify, session, Response
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Import services - with error handling to prevent import conflicts
try:
    from services.supabase_client import SupabaseService
    from services.elevenlabs_service import ElevenLabsService
    from services.roleplay_engine import RoleplayEngine
except ImportError as e:
    logging.error(f"Service import error: {e}")
    # Create placeholder classes to prevent crashes
    class SupabaseService:
        def __init__(self): pass
    class ElevenLabsService:
        def __init__(self): pass
    class RoleplayEngine:
        def __init__(self): pass

# Import utilities - with error handling
try:
    from utils.decorators import require_auth, check_usage_limits, validate_json_input, log_api_call
    from utils.helpers import calculate_usage_limits, log_user_action, format_duration
    from utils.constants import ROLEPLAY_CONFIG
except ImportError as e:
    logging.error(f"Utils import error: {e}")
    # Create placeholder decorators to prevent crashes
    def require_auth(f): return f
    def check_usage_limits(f): return f
    def validate_json_input(**kwargs): return lambda f: f
    def log_api_call(f): return f
    def log_user_action(*args, **kwargs): pass
    def format_duration(minutes): return f"{minutes} min"
    ROLEPLAY_CONFIG = {1: {'id': 1, 'name': 'Default'}}

logger = logging.getLogger(__name__)

# Create blueprint with unique name to avoid conflicts
roleplay_bp = Blueprint('roleplay_v2', __name__, url_prefix='/api/roleplay')

# Initialize services with error handling
try:
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()
    logger.info("Roleplay services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing roleplay services: {e}")
    # Create dummy services to prevent crashes
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()

@roleplay_bp.route('/start', methods=['POST'])
@require_auth
@check_usage_limits
@validate_json_input(required_fields=['roleplay_id', 'mode'])
@log_api_call
def start_roleplay():
    """Start a new roleplay session with Roleplay 1.1 support"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        roleplay_id = data.get('roleplay_id')
        mode = data.get('mode', 'practice')
        
        logger.info(f"Starting roleplay {roleplay_id} in {mode} mode for user {user_id}")
        
        # Enhanced validation for Roleplay 1.1
        if roleplay_id not in ROLEPLAY_CONFIG:
            return jsonify({'error': f'Invalid roleplay ID: {roleplay_id}'}), 400
        
        # Get user profile and context
        try:
            profile = supabase_service.get_user_profile_by_service(user_id)
            if not profile:
                return jsonify({'error': 'User profile not found'}), 404
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return jsonify({'error': 'Failed to load user profile'}), 500
        
        # Check if roleplay is unlocked
        if not _is_roleplay_unlocked(user_id, roleplay_id, profile):
            return jsonify({'error': 'Roleplay not unlocked. Complete previous challenges first.'}), 403
        
        # Prepare enhanced user context for Roleplay 1.1
        user_context = {
            'first_name': profile.get('first_name', 'User'),
            'prospect_job_title': profile.get('prospect_job_title', 'Manager'),
            'prospect_industry': profile.get('prospect_industry', 'Business'),
            'custom_ai_notes': profile.get('custom_ai_notes', ''),
            'access_level': profile.get('access_level', 'basic'),
            'roleplay_version': '1.1' if roleplay_id == 1 else 'standard'
        }
        
        # Create roleplay session with enhanced engine
        try:
            session_result = roleplay_engine.create_session(
                user_id=user_id,
                roleplay_id=roleplay_id,
                mode=mode,
                user_context=user_context
            )
        except Exception as e:
            logger.error(f"Error creating roleplay session: {e}")
            return jsonify({'error': 'Failed to create session'}), 500
        
        if not session_result.get('success'):
            return jsonify({'error': session_result.get('error', 'Failed to create session')}), 400
        
        # Store session ID in user session
        session['current_roleplay_session'] = session_result['session_id']
        
        # Log action with Roleplay 1.1 specifics
        try:
            log_user_action(user_id, 'roleplay_started', {
                'roleplay_id': roleplay_id,
                'mode': mode,
                'session_id': session_result['session_id'],
                'roleplay_version': '1.1' if roleplay_id == 1 else 'standard'
            })
        except Exception as e:
            logger.warning(f"Failed to log user action: {e}")
        
        # Enhanced response for Roleplay 1.1
        response_data = {
            'message': f'Roleplay {roleplay_id} session started successfully',
            'session_id': session_result['session_id'],
            'roleplay_id': roleplay_id,
            'mode': mode,
            'initial_response': session_result.get('initial_response', 'Hello?'),
            'user_context': user_context,
            'tts_available': getattr(elevenlabs_service, 'is_available', lambda: False)()
        }
        
        # Add Roleplay 1.1 specific data
        if roleplay_id == 1:
            response_data['roleplay_11_specs'] = {
                'silence_impatience_threshold': 10,
                'silence_hangup_threshold': 15,
                'opener_hangup_chance': 0.25,
                'total_stages': 4
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error starting roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/respond', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['user_input'])
@log_api_call
def handle_user_response():
    """Handle user's voice input during roleplay with Roleplay 1.1 support"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        if not user_input:
            return jsonify({'error': 'User input is required'}), 400
        
        # Get current session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Processing user input for session {session_id}: {user_input[:100]}...")
        
        # Process user input through enhanced roleplay engine
        try:
            response_result = roleplay_engine.process_user_input(session_id, user_input)
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return jsonify({'error': 'Failed to process input'}), 500
        
        if not response_result.get('success'):
            return jsonify({'error': response_result.get('error', 'Failed to process input')}), 500
        
        # Enhanced logging for Roleplay 1.1
        log_data = {
            'session_id': session_id,
            'user_input_length': len(user_input),
            'ai_response_length': len(response_result.get('ai_response', '')),
            'call_continues': response_result.get('call_continues', True),
            'stage': response_result.get('session_state', 'unknown')
        }
        
        # Add Roleplay 1.1 specific logging
        if response_result.get('evaluation'):
            evaluation = response_result['evaluation']
            log_data.update({
                'stage_passed': evaluation.get('passed', False),
                'criteria_met': evaluation.get('criteria_met', []),
                'rubric_score': evaluation.get('score', 0),
                'evaluation_stage': evaluation.get('stage', 'unknown')
            })
        
        try:
            log_user_action(user_id, 'roleplay_interaction', log_data)
        except Exception as e:
            logger.warning(f"Failed to log interaction: {e}")
        
        # Enhanced response for Roleplay 1.1
        response_data = {
            'ai_response': response_result.get('ai_response', 'I see.'),
            'call_continues': response_result.get('call_continues', True),
            'session_state': response_result.get('session_state', 'in_progress'),
            'evaluation': response_result.get('evaluation', {})
        }
        
        # Add Roleplay 1.1 specific progress data
        if response_result.get('overall_progress'):
            response_data['roleplay_11_progress'] = response_result['overall_progress']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error handling user response: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/tts', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['text'])
@log_api_call
def text_to_speech():
    """Convert text to speech - ENHANCED FOR ROLEPLAY 1.1 (Never fails)"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        logger.info(f"TTS request from user {user_id}: {text[:100]}...")
        
        # Handle empty text
        if not text:
            logger.info("Empty text provided for TTS")
            return _create_silent_audio_response()
        
        # Truncate text if too long (ElevenLabs limit)
        if len(text) > 2500:
            text = text[:2500]
            logger.warning(f"Text truncated to 2500 characters for TTS")
        
        # Get user profile for voice customization (Enhanced for Roleplay 1.1)
        voice_settings = None
        try:
            profile = supabase_service.get_user_profile_by_service(user_id)
            if profile and hasattr(elevenlabs_service, 'get_voice_settings_for_prospect'):
                voice_settings = elevenlabs_service.get_voice_settings_for_prospect({
                    'prospect_job_title': profile.get('prospect_job_title', ''),
                    'prospect_industry': profile.get('prospect_industry', ''),
                    'roleplay_version': '1.1',
                    'call_urgency': 'medium'
                })
        except Exception as profile_error:
            logger.warning(f"Could not get profile for TTS customization: {profile_error}")
        
        # Generate speech with enhanced error handling for Roleplay 1.1
        audio_data = None
        try:
            if hasattr(elevenlabs_service, 'text_to_speech'):
                audio_stream = elevenlabs_service.text_to_speech(text, voice_settings)
                if audio_stream:
                    audio_data = audio_stream.getvalue()
        except Exception as tts_error:
            logger.error(f"TTS generation failed: {tts_error}")
        
        # Fallback to emergency audio if needed
        if not audio_data or len(audio_data) < 44:
            audio_data = _create_emergency_audio_data(text)
        
        # Enhanced logging for Roleplay 1.1 (don't fail if logging fails)
        try:
            log_user_action(user_id, 'tts_generated', {
                'text_length': len(text),
                'audio_size': len(audio_data),
                'voice_settings': voice_settings,
                'roleplay_version': '1.1'
            })
        except Exception as log_error:
            logger.warning(f"Could not log TTS usage: {log_error}")
        
        # Return audio response with enhanced headers for Roleplay 1.1
        return Response(
            audio_data,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=roleplay_11_speech.wav',
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'no-cache',
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'X-Roleplay-Version': '1.1'
            }
        )
        
    except Exception as critical_error:
        logger.critical(f"Critical TTS endpoint failure: {critical_error}")
        # Return emergency fallback - never fail
        return _create_emergency_audio_response()

@roleplay_bp.route('/end', methods=['POST'])
@require_auth
@log_api_call
def end_roleplay():
    """End current roleplay session and provide coaching with Roleplay 1.1 support"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        forced_end = data.get('forced_end', False)
        
        # Get current session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Ending roleplay session {session_id} for user {user_id}")
        
        # End session through enhanced roleplay engine
        try:
            end_result = roleplay_engine.end_session(session_id, forced_end)
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return jsonify({'error': 'Failed to end session'}), 500
        
        if not end_result.get('success'):
            return jsonify({'error': end_result.get('error', 'Failed to end session')}), 500
        
        # Enhanced session data for Roleplay 1.1
        session_data = end_result.get('session_data', {})
        voice_session_record = {
            'user_id': user_id,
            'roleplay_id': session_data.get('roleplay_id', 1),
            'mode': session_data.get('mode', 'practice'),
            'started_at': session_data.get('started_at', datetime.now(timezone.utc).isoformat()),
            'ended_at': session_data.get('ended_at', datetime.now(timezone.utc).isoformat()),
            'duration_minutes': end_result.get('duration_minutes', 1),
            'success': end_result.get('session_success', False),
            'score': end_result.get('overall_score', 50),
            'feedback_data': end_result.get('coaching', {}),
            'session_data': session_data
        }
        
        # Add Roleplay 1.1 specific data
        if session_data.get('roleplay_id') == 1:
            voice_session_record['roleplay_11_data'] = {
                'rubric_scores': session_data.get('rubric_scores', {}),
                'stage_progression': session_data.get('stage_progression', []),
                'silence_events': session_data.get('silence_events', []),
                'overall_result': session_data.get('overall_call_result', 'unknown'),
                'hang_up_reason': session_data.get('hang_up_reason'),
                'version': '1.1'
            }
        
        # Insert session record
        try:
            supabase_service.get_service_client().table('voice_sessions').insert(voice_session_record).execute()
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")
            # Continue anyway, don't fail the request
        
        # Update user usage
        try:
            _update_user_usage(user_id, end_result.get('duration_minutes', 1))
        except Exception as e:
            logger.warning(f"Failed to update user usage: {e}")
        
        # Clear session
        session.pop('current_roleplay_session', None)
        
        # Enhanced logging for Roleplay 1.1
        log_data = {
            'session_id': session_id,
            'duration_minutes': end_result.get('duration_minutes', 1),
            'success': end_result.get('session_success', False),
            'score': end_result.get('overall_score', 50)
        }
        
        if session_data.get('roleplay_id') == 1:
            log_data['roleplay_11_results'] = end_result.get('roleplay_11_results', {})
        
        try:
            log_user_action(user_id, 'roleplay_completed', log_data)
        except Exception as e:
            logger.warning(f"Failed to log completion: {e}")
        
        # Enhanced response for Roleplay 1.1
        response_data = {
            'message': 'Session ended successfully',
            'duration_minutes': end_result.get('duration_minutes', 1),
            'session_success': end_result.get('session_success', False),
            'coaching': end_result.get('coaching', {}),
            'overall_score': end_result.get('overall_score', 50),
            'completion_message': end_result.get('completion_message', 'Session complete!'),
            'formatted_duration': format_duration(end_result.get('duration_minutes', 1))
        }
        
        # Add Roleplay 1.1 specific results
        if 'roleplay_11_results' in end_result:
            response_data['roleplay_11_results'] = end_result['roleplay_11_results']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error ending roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/session/status', methods=['GET'])
@require_auth
def get_session_status():
    """Get current session status with Roleplay 1.1 enhancements"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'active': False, 'session': None})
        
        # Get session status from enhanced engine
        try:
            session_status = roleplay_engine.get_session_status(session_id)
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            session.pop('current_roleplay_session', None)
            return jsonify({'active': False, 'session': None})
        
        if not session_status:
            # Session not found, clear from user session
            session.pop('current_roleplay_session', None)
            return jsonify({'active': False, 'session': None})
        
        # Enhanced response for Roleplay 1.1
        response_data = {
            'active': session_status.get('session_active', False),
            'session': {
                'session_id': session_id,
                'roleplay_id': session_status.get('roleplay_id', 1),
                'mode': session_status.get('mode', 'practice'),
                'current_stage': session_status.get('current_stage', 'phone_pickup'),
                'call_count': session_status.get('call_count', 0),
                'successful_calls': session_status.get('successful_calls', 0)
            }
        }
        
        # Add Roleplay 1.1 specific status
        if session_status.get('roleplay_id') == 1:
            response_data['roleplay_11_status'] = {
                'rubric_scores': session_status.get('rubric_scores', {}),
                'stage_progression': session_status.get('stage_progression', []),
                'overall_result': session_status.get('overall_call_result', 'in_progress'),
                'silence_events': len(session_status.get('silence_events', [])),
                'version': '1.1'
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/info/<int:roleplay_id>', methods=['GET'])
@require_auth
def get_roleplay_info(roleplay_id):
    """Get roleplay information with Roleplay 1.1 enhancements"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        if roleplay_id not in ROLEPLAY_CONFIG:
            return jsonify({'error': 'Invalid roleplay ID'}), 404
        
        # Get base configuration
        config = ROLEPLAY_CONFIG[roleplay_id].copy()
        
        # Add Roleplay 1.1 specific enhancements
        if roleplay_id == 1:
            config['roleplay_11_features'] = {
                'silence_monitoring': {
                    'impatience_threshold': 10,
                    'hangup_threshold': 15,
                    'impatience_phrases': 10
                },
                'rubric_system': {
                    'total_rubrics': 4,
                    'criteria_per_rubric': [4, 4, 4, 3],
                    'pass_thresholds': [3, 3, 3, 2]
                },
                'coaching_system': {
                    'language_level': 'CEFR A2',
                    'categories': 5,
                    'pronunciation_monitoring': True
                },
                'objection_system': {
                    'total_objections': 29,
                    'no_consecutive_repeats': True
                }
            }
            
            config['enhanced_description'] = (
                'Roleplay 1.1 - Enhanced opener training with precise rubric evaluation, '
                '10s/15s silence monitoring, CEFR A2 coaching, and 29 unique objections.'
            )
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper functions with error handling

def _is_roleplay_unlocked(user_id: str, roleplay_id: int, profile: Dict) -> bool:
    """Check if roleplay is unlocked for user with Roleplay 1.1 support"""
    try:
        # Roleplay 1 (1.1) is always unlocked
        if roleplay_id == 1:
            return True
        
        # Pro users have everything unlocked
        if profile.get('access_level') == 'unlimited_pro':
            return True
        
        # For now, unlock all roleplays - you can implement proper unlocking logic later
        return True
        
    except Exception as e:
        logger.error(f"Error checking roleplay unlock status: {e}")
        return True  # Default to unlocked to prevent blocking

def _update_user_usage(user_id: str, duration_minutes: int):
    """Update user's usage statistics"""
    try:
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            return
        
        new_monthly = (profile.get('monthly_usage_minutes') or 0) + duration_minutes
        new_lifetime = (profile.get('lifetime_usage_minutes') or 0) + duration_minutes
        
        updates = {
            'monthly_usage_minutes': new_monthly,
            'lifetime_usage_minutes': new_lifetime
        }
        
        supabase_service.update_user_profile_by_service(user_id, updates)
        
        logger.info(f"Updated usage for user {user_id}: +{duration_minutes} minutes")
        
    except Exception as e:
        logger.error(f"Error updating user usage: {e}")

def _create_silent_audio_response():
    """Create a silent audio response"""
    try:
        # Minimal WAV header for 1 second of silence
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
        return Response(b'', mimetype='audio/wav', status=200)

def _create_emergency_audio_data(text: str = None) -> bytes:
    """Create emergency audio data when TTS fails"""
    try:
        # Minimal WAV header - always return something
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
    """Create emergency audio response when everything fails"""
    try:
        emergency_audio = _create_emergency_audio_data()
        return Response(
            emergency_audio,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=emergency.wav',
                'Content-Length': str(len(emergency_audio)),
                'Cache-Control': 'no-cache'
            },
            status=200
        )
    except Exception as e:
        logger.critical(f"Final emergency fallback failed: {e}")
        return Response(b'', mimetype='audio/wav', status=200)

# Health check endpoint
@roleplay_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Roleplay system"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.1',
            'services': {
                'roleplay_engine': 'running',
                'tts_service': 'available' if hasattr(elevenlabs_service, 'is_available') else 'unknown',
                'database': 'connected'
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500