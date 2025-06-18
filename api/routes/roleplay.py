# ===== FIXED API/ROUTES/ROLEPLAY.PY (TTS ERROR HANDLING) =====
from flask import Blueprint, request, jsonify, session, Response
from services.supabase_client import SupabaseService
from services.elevenlabs_service import ElevenLabsService
from services.roleplay_engine import RoleplayEngine
from utils.decorators import require_auth, check_usage_limits, validate_json_input, log_api_call
from utils.helpers import calculate_usage_limits, log_user_action, format_duration
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
roleplay_bp = Blueprint('roleplay', __name__)

# Initialize services
supabase_service = SupabaseService()
elevenlabs_service = ElevenLabsService()
roleplay_engine = RoleplayEngine()

@roleplay_bp.route('/start', methods=['POST'])
@require_auth
@check_usage_limits
@validate_json_input(required_fields=['roleplay_id', 'mode'])
@log_api_call
def start_roleplay():
    """Start a new roleplay session"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        roleplay_id = data.get('roleplay_id')
        mode = data.get('mode', 'practice')
        
        logger.info(f"Starting roleplay {roleplay_id} in {mode} mode for user {user_id}")
        
        # Get user profile and context
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            return jsonify({'error': 'User profile not found'}), 404
        
        # Check if roleplay is unlocked
        if not _is_roleplay_unlocked(user_id, roleplay_id, profile):
            return jsonify({'error': 'Roleplay not unlocked. Complete previous challenges first.'}), 403
        
        # Prepare user context
        user_context = {
            'first_name': profile['first_name'],
            'prospect_job_title': profile['prospect_job_title'],
            'prospect_industry': profile['prospect_industry'],
            'custom_ai_notes': profile.get('custom_ai_notes', ''),
            'access_level': profile['access_level']
        }
        
        # Create roleplay session
        session_result = roleplay_engine.create_session(
            user_id=user_id,
            roleplay_id=roleplay_id,
            mode=mode,
            user_context=user_context
        )
        
        if not session_result['success']:
            return jsonify({'error': session_result['error']}), 400
        
        # Store session ID in user session
        session['current_roleplay_session'] = session_result['session_id']
        
        # Log action
        log_user_action(user_id, 'roleplay_started', {
            'roleplay_id': roleplay_id,
            'mode': mode,
            'session_id': session_result['session_id']
        })
        
        return jsonify({
            'message': 'Roleplay session started successfully',
            'session_id': session_result['session_id'],
            'roleplay_id': roleplay_id,
            'mode': mode,
            'initial_response': session_result['initial_response'],
            'user_context': user_context,
            'tts_available': elevenlabs_service.is_available()
        })
        
    except Exception as e:
        logger.error(f"Error starting roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/respond', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['user_input'])
@log_api_call
def handle_user_response():
    """Handle user's voice input during roleplay"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        user_id = session['user_id']
        
        if not user_input:
            return jsonify({'error': 'User input is required'}), 400
        
        # Get current session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Processing user input for session {session_id}: {user_input[:100]}...")
        
        # Process user input through roleplay engine
        response_result = roleplay_engine.process_user_input(session_id, user_input)
        
        if not response_result['success']:
            return jsonify({'error': response_result['error']}), 500
        
        # Log the interaction
        log_user_action(user_id, 'roleplay_interaction', {
            'session_id': session_id,
            'user_input_length': len(user_input),
            'ai_response_length': len(response_result.get('ai_response', '')),
            'call_continues': response_result.get('call_continues', True)
        })
        
        return jsonify({
            'ai_response': response_result['ai_response'],
            'call_continues': response_result['call_continues'],
            'session_state': response_result.get('session_state', 'in_progress'),
            'evaluation': response_result.get('evaluation', {})
        })
        
    except Exception as e:
        logger.error(f"Error handling user response: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/tts', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['text'])
@log_api_call
def text_to_speech():
    """Convert text to speech using ElevenLabs with bulletproof error handling"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        user_id = session['user_id']
        
        if not text:
            # Return silent audio for empty text instead of error
            logger.warning("Empty text provided for TTS")
            audio_stream = elevenlabs_service._generate_silent_audio()
            audio_data = audio_stream.getvalue() if audio_stream else b''
            
            return Response(
                audio_data,
                mimetype='audio/wav',
                headers={
                    'Content-Disposition': 'inline; filename=silence.wav',
                    'Content-Length': str(len(audio_data)),
                    'Cache-Control': 'no-cache'
                }
            )
        
        if len(text) > 2500:  # ElevenLabs limit
            # Truncate text instead of failing
            text = text[:2500]
            logger.warning(f"Text truncated to 2500 characters for TTS")
        
        logger.info(f"Generating TTS for user {user_id}: {text[:100]}...")
        
        # Get user profile for voice customization
        profile = supabase_service.get_user_profile_by_service(user_id)
        voice_settings = None
        
        if profile:
            voice_settings = elevenlabs_service.get_voice_settings_for_prospect({
                'prospect_job_title': profile.get('prospect_job_title', ''),
                'prospect_industry': profile.get('prospect_industry', '')
            })
        
        # Generate speech - this now ALWAYS returns audio
        audio_stream = elevenlabs_service.text_to_speech(text, voice_settings)
        
        # The service now ALWAYS returns a BytesIO object, never None
        if not audio_stream:
            logger.error("TTS service returned None - using emergency fallback")
            audio_stream = elevenlabs_service._generate_silent_audio()
        
        # Get audio data
        audio_data = audio_stream.getvalue()
        
        # Ensure we have some audio data
        if not audio_data or len(audio_data) < 44:  # Less than WAV header size
            logger.warning("Audio data too small, generating emergency fallback")
            audio_stream = elevenlabs_service._generate_fallback_audio(text)
            audio_data = audio_stream.getvalue()
        
        # Log TTS usage
        log_user_action(user_id, 'tts_generated', {
            'text_length': len(text),
            'audio_size': len(audio_data),
            'voice_settings': voice_settings,
            'tts_available': elevenlabs_service.is_available()
        })
        
        # Return audio - this should NEVER fail
        return Response(
            audio_data,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': 'inline; filename=speech.wav',
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'no-cache',
                'Accept-Ranges': 'bytes'
            }
        )
        
    except Exception as e:
        logger.error(f"Critical error in text-to-speech: {e}")
        
        # Emergency fallback - NEVER let this endpoint fail
        try:
            # Create minimal emergency audio
            silent_audio = elevenlabs_service._generate_silent_audio()
            audio_data = silent_audio.getvalue() if silent_audio else b''
            
            # If even that fails, create absolute minimal WAV
            if not audio_data:
                # Create the most basic WAV file possible
                header = b'RIFF\x2c\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                audio_data = header
            
            return Response(
                audio_data,
                mimetype='audio/wav',
                headers={
                    'Content-Disposition': 'inline; filename=emergency.wav',
                    'Content-Length': str(len(audio_data))
                }
            )
            
        except Exception as critical_error:
            logger.critical(f"Critical TTS failure: {critical_error}")
            # Return empty response as absolute last resort
            return Response(
                b'',
                mimetype='application/octet-stream',
                status=200  # Still return 200 to avoid breaking the flow
            )

@roleplay_bp.route('/end', methods=['POST'])
@require_auth
@log_api_call
def end_roleplay():
    """End current roleplay session and provide coaching"""
    try:
        data = request.get_json() or {}
        user_id = session['user_id']
        forced_end = data.get('forced_end', False)
        
        # Get current session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Ending roleplay session {session_id} for user {user_id}")
        
        # End session through roleplay engine
        end_result = roleplay_engine.end_session(session_id, forced_end)
        
        if not end_result['success']:
            return jsonify({'error': end_result['error']}), 500
        
        # Save session to database
        session_data = end_result['session_data']
        voice_session_record = {
            'user_id': user_id,
            'roleplay_id': session_data['roleplay_id'],
            'mode': session_data['mode'],
            'started_at': session_data['started_at'],
            'ended_at': end_result['session_data'].get('ended_at'),
            'duration_minutes': end_result['duration_minutes'],
            'success': end_result['session_success'],
            'score': end_result['overall_score'],
            'feedback_data': end_result['coaching'],
            'session_data': session_data
        }
        
        # Insert session record
        try:
            supabase_service.get_service_client().table('voice_sessions').insert(voice_session_record).execute()
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")
            # Continue anyway, don't fail the request
        
        # Update user usage
        _update_user_usage(user_id, end_result['duration_minutes'])
        
        # Clear session
        session.pop('current_roleplay_session', None)
        
        # Log completion
        log_user_action(user_id, 'roleplay_completed', {
            'session_id': session_id,
            'duration_minutes': end_result['duration_minutes'],
            'success': end_result['session_success'],
            'score': end_result['overall_score']
        })
        
        return jsonify({
            'message': 'Session ended successfully',
            'duration_minutes': end_result['duration_minutes'],
            'session_success': end_result['session_success'],
            'coaching': end_result['coaching'],
            'overall_score': end_result['overall_score'],
            'completion_message': end_result['completion_message'],
            'formatted_duration': format_duration(end_result['duration_minutes'])
        })
        
    except Exception as e:
        logger.error(f"Error ending roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/session/status', methods=['GET'])
@require_auth
def get_session_status():
    """Get current session status"""
    try:
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'active': False, 'session': None})
        
        # Get session status from engine
        session_status = roleplay_engine.get_session_status(session_id)
        
        if not session_status:
            # Session not found, clear from user session
            session.pop('current_roleplay_session', None)
            return jsonify({'active': False, 'session': None})
        
        return jsonify({
            'active': session_status.get('session_active', False),
            'session': {
                'session_id': session_id,
                'roleplay_id': session_status.get('roleplay_id'),
                'mode': session_status.get('mode'),
                'current_stage': session_status.get('current_stage'),
                'call_count': session_status.get('call_count', 0),
                'successful_calls': session_status.get('successful_calls', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/session/abort', methods=['POST'])
@require_auth
def abort_session():
    """Abort current session without saving"""
    try:
        session_id = session.get('current_roleplay_session')
        if session_id:
            # Force end session
            roleplay_engine.end_session(session_id, forced_end=True)
            session.pop('current_roleplay_session', None)
            
            log_user_action(session['user_id'], 'roleplay_aborted', {
                'session_id': session_id
            })
        
        return jsonify({'message': 'Session aborted successfully'})
        
    except Exception as e:
        logger.error(f"Error aborting session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/info/<int:roleplay_id>', methods=['GET'])
@require_auth
def get_roleplay_info(roleplay_id):
    """Get roleplay information"""
    try:
        # Define roleplay configurations
        roleplay_configs = {
            1: {
                'id': 1,
                'name': 'Opener + Early Objections',
                'description': 'Master call openings and handle early objections with confidence',
                'difficulty': 'Beginner',
                'industry': 'Technology',
                'job_title': 'CTO',
                'estimated_duration': '5-10 minutes'
            },
            2: {
                'id': 2,
                'name': 'Pitch + Objections + Close',
                'description': 'Perfect your pitch and close more meetings',
                'difficulty': 'Intermediate',
                'industry': 'Finance',
                'job_title': 'VP of Sales',
                'estimated_duration': '10-15 minutes'
            },
            3: {
                'id': 3,
                'name': 'Warm-up Challenge',
                'description': '25 rapid-fire questions to sharpen your skills',
                'difficulty': 'Quick',
                'industry': 'Healthcare',
                'job_title': 'Director',
                'estimated_duration': '3-5 minutes'
            },
            4: {
                'id': 4,
                'name': 'Full Cold Call Simulation',
                'description': 'Complete end-to-end cold call practice',
                'difficulty': 'Advanced',
                'industry': 'Manufacturing',
                'job_title': 'Operations Manager',
                'estimated_duration': '15-20 minutes'
            },
            5: {
                'id': 5,
                'name': 'Power Hour Challenge',
                'description': '10 consecutive calls to test your endurance',
                'difficulty': 'Expert',
                'industry': 'Education',
                'job_title': 'Principal',
                'estimated_duration': '45-60 minutes'
            }
        }
        
        if roleplay_id not in roleplay_configs:
            return jsonify({'error': 'Invalid roleplay ID'}), 404
        
        return jsonify(roleplay_configs[roleplay_id])
        
    except Exception as e:
        logger.error(f"Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper functions
def _is_roleplay_unlocked(user_id: str, roleplay_id: int, profile: Dict) -> bool:
    """Check if roleplay is unlocked for user"""
    try:
        # Roleplay 1 is always unlocked
        if roleplay_id == 1:
            return True
        
        # Pro users have everything unlocked
        if profile.get('access_level') == 'unlimited_pro':
            return True
        
        # Check user progress
        progress = supabase_service.get_user_progress(user_id)
        roleplay_progress = next((p for p in progress if p.get('roleplay_id') == roleplay_id), None)
        
        if not roleplay_progress or not roleplay_progress.get('unlocked_at'):
            return False
        
        # Check if unlock has expired (for Basic users)
        access_level = profile.get('access_level', 'limited_trial')
        if access_level == 'unlimited_basic':
            expires_at = roleplay_progress.get('expires_at')
            if expires_at:
                try:
                    from utils.helpers import parse_iso_datetime
                    expire_time = parse_iso_datetime(expires_at)
                    current_time = datetime.now(timezone.utc)
                    return current_time < expire_time
                except:
                    return True  # Default to unlocked if can't parse
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking roleplay unlock status: {e}")
        return False

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

# Cleanup endpoint for expired sessions
@roleplay_bp.route('/cleanup', methods=['POST'])
def cleanup_sessions():
    """Cleanup expired sessions (internal endpoint)"""
    try:
        # Only allow from localhost or with special header
        if request.remote_addr not in ['127.0.0.1', 'localhost'] and request.headers.get('X-Internal-Request') != 'true':
            return jsonify({'error': 'Not authorized'}), 403
        
        roleplay_engine.cleanup_expired_sessions()
        return jsonify({'message': 'Cleanup completed'})
        
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        return jsonify({'error': 'Internal server error'}), 500