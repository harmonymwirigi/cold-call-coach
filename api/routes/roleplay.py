# ===== api/routes/roleplay.py (Updated Routes) =====

from flask import Blueprint, request, jsonify, session, Response, redirect, render_template, url_for
import logging
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
    # Create placeholder classes (same as before)

# Import utilities with error handling  
try:
    from utils.decorators import require_auth, check_usage_limits, validate_json_input, log_api_call
    from utils.helpers import log_user_action, format_duration
    from utils.constants import ROLEPLAY_CONFIG
except ImportError as e:
    logger.error(f"Utils import error: {e}")
    # Create placeholder functions (same as before)

# Create blueprint
roleplay_bp = Blueprint('roleplay', __name__, url_prefix='/api/roleplay')

# Initialize services
try:
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()
    progress_service = UserProgressService()
    logger.info("Roleplay services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing services: {e}")
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()



@roleplay_bp.route('/1/select', methods=['GET'])
def roleplay_1_selection():
    """Show Roleplay 1 selection page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Get user progress for Roleplay 1 modes
        user_progress = progress_service.get_user_roleplay_progress(user_id, ['1.1', '1.2', '1.3'])
        
        return render_template(
            'roleplay/roleplay-1-selection.html',
            user_progress=user_progress,
            page_title="Roleplay 1: Choose Your Mode"
        )
        
    except Exception as e:
        logger.error(f"Error showing roleplay 1 selection: {e}")
        return redirect(url_for('dashboard_page'))
@roleplay_bp.route('/start', methods=['POST'])
def start_roleplay():
    """Start roleplay session with progress tracking"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        roleplay_id = data.get('roleplay_id')
        mode = data.get('mode', 'practice')
        
        # Validate roleplay access
        access_check = progress_service.check_roleplay_access(user_id, roleplay_id)
        if not access_check['allowed']:
            return jsonify({
                'error': access_check['reason'],
                'requirements': access_check.get('requirements', [])
            }), 403
        
        logger.info(f"Starting roleplay: {roleplay_id}, mode={mode}, user={user_id}")
        
        # Get user profile and context
        profile = supabase_service.get_user_profile_by_service(user_id)
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
        session_result = roleplay_engine.create_session(
            user_id=user_id,
            roleplay_id=roleplay_id,
            mode=mode,
            user_context=user_context
        )
        
        if not session_result.get('success'):
            return jsonify({'error': session_result.get('error', 'Failed to create session')}), 500
        
        # Store session ID
        session['current_roleplay_session'] = session_result['session_id']
        
        # Log start attempt
        progress_service.log_roleplay_attempt(user_id, roleplay_id, session_result['session_id'])
        
        response_data = {
            'message': f'Roleplay {roleplay_id} session started successfully',
            'session_id': session_result['session_id'],
            'roleplay_id': roleplay_id,
            'mode': mode,
            'initial_response': session_result.get('initial_response', 'Hello?'),
            'roleplay_info': session_result.get('roleplay_info', {}),
            'tts_available': elevenlabs_service.is_available() if hasattr(elevenlabs_service, 'is_available') else False,
            'marathon_status': session_result.get('marathon_status')
        }
        
        logger.info(f"Roleplay {roleplay_id} session started: {session_result['session_id']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error starting roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/respond', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['user_input'])
@log_api_call
def handle_user_response():
    """Handle user input during roleplay"""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if not user_input:
            return jsonify({'error': 'User input is required'}), 400
        
        # Get session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Processing user input for session {session_id}: '{user_input[:50]}...'")
        
        # Process input through roleplay engine
        response_result = roleplay_engine.process_user_input(session_id, user_input)
        
        if not response_result.get('success'):
            error_msg = response_result.get('error', 'Failed to process input')
            logger.error(f"Input processing failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Log interaction
        try:
            log_user_action(user_id, 'roleplay_interaction', {
                'session_id': session_id,
                'user_input_length': len(user_input),
                'ai_response_length': len(response_result.get('ai_response', '')),
                'call_continues': response_result.get('call_continues', True),
                'stage': response_result.get('session_state', 'unknown'),
                'evaluation': response_result.get('evaluation', {}),
                'marathon_status': response_result.get('marathon_status')
            })
        except Exception as e:
            logger.warning(f"Failed to log interaction: {e}")
        
        # Return response
        response_data = {
            'ai_response': response_result.get('ai_response', 'I see.'),
            'call_continues': response_result.get('call_continues', True),
            'session_state': response_result.get('session_state', 'in_progress'),
            'evaluation': response_result.get('evaluation', {}),
            
            # Marathon specific fields
            'marathon_status': response_result.get('marathon_status'),
            'marathon_complete': response_result.get('marathon_complete', False),
            'marathon_passed': response_result.get('marathon_passed'),
            'call_result': response_result.get('call_result'),
            'new_call_started': response_result.get('new_call_started', False),
            'current_call': response_result.get('current_call'),
            'total_calls': response_result.get('total_calls'),
            
            # Practice mode specific fields
            'turn_count': response_result.get('turn_count'),
            'conversation_quality': response_result.get('conversation_quality')
        }
        
        logger.info(f"Response sent: '{response_data['ai_response'][:50]}...' | Continues: {response_data['call_continues']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error handling user response: {e}")
        return jsonify({'error': 'Internal server error'}), 500
@roleplay_bp.route('/end', methods=['POST'])
def end_roleplay():
    """End roleplay session with AI scoring and progress tracking"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        forced_end = data.get('forced_end', False)
        session_id = session.get('current_roleplay_session')
        
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Ending roleplay session {session_id} for user {user_id}")
        
        # End session and get results
        end_result = roleplay_engine.end_session(session_id, forced_end)
        
        if not end_result.get('success'):
            return jsonify({'error': end_result.get('error', 'Failed to end session')}), 500
        
        # Extract session data
        session_data = end_result.get('session_data', {})
        roleplay_id = session_data.get('roleplay_id', '1.1')
        
        # ===== NEW: AI-POWERED SCORING =====
        ai_evaluation = None
        final_score = end_result.get('overall_score', 50)
        
        # Use AI for detailed evaluation if available
        if roleplay_engine.is_openai_available():
            try:
                ai_evaluation = roleplay_engine.openai_service.generate_coaching_feedback(
                    session_data.get('conversation_history', []),
                    session_data.get('rubric_scores', {}),
                    session_data.get('user_context', {})
                )
                
                if ai_evaluation.get('success'):
                    final_score = ai_evaluation.get('score', final_score)
                    logger.info(f"AI evaluation successful: {final_score}/100")
                
            except Exception as ai_error:
                logger.warning(f"AI evaluation failed: {ai_error}")
        
        # ===== NEW: Save to Database with Detailed Tracking =====
        completion_data = {
            'user_id': user_id,
            'roleplay_id': roleplay_id,
            'session_id': session_id,
            'mode': session_data.get('mode', 'practice'),
            'started_at': session_data.get('started_at'),
            'ended_at': session_data.get('ended_at'),
            'duration_minutes': end_result.get('duration_minutes', 1),
            'success': end_result.get('session_success', False),
            'score': final_score,
            'ai_evaluation': ai_evaluation,
            'coaching_feedback': end_result.get('coaching', {}),
            'conversation_data': {
                'total_turns': len(session_data.get('conversation_history', [])),
                'user_turns': session_data.get('user_turn_count', 0),
                'stages_completed': session_data.get('stages_completed', []),
                'conversation_quality': session_data.get('conversation_quality', 0)
            },
            'marathon_results': end_result.get('marathon_results'),  # For Marathon mode
            'rubric_scores': session_data.get('rubric_scores', {}),
            'forced_end': forced_end
        }
        
        # Save completion record
        try:
            completion_id = progress_service.save_roleplay_completion(completion_data)
            logger.info(f"Completion saved with ID: {completion_id}")
        except Exception as db_error:
            logger.error(f"Failed to save completion: {db_error}")
        
        # ===== NEW: Update User Progress and Check Unlocks =====
        progress_update = progress_service.update_user_progress(user_id, roleplay_id, completion_data)
        
        # Check for new unlocks
        unlocks = progress_service.check_new_unlocks(user_id)
        if unlocks:
            logger.info(f"New unlocks for user {user_id}: {unlocks}")
        
        # Clear session
        session.pop('current_roleplay_session', None)
        
        # Prepare response
        response_data = {
            'message': 'Roleplay session ended successfully',
            'duration_minutes': end_result.get('duration_minutes', 1),
            'session_success': end_result.get('session_success', False),
            'coaching': end_result.get('coaching', {}),
            'overall_score': final_score,
            'ai_scored': bool(ai_evaluation and ai_evaluation.get('success')),
            'completion_message': f"Session complete! Score: {final_score}/100",
            'roleplay_type': end_result.get('roleplay_type', 'practice'),
            'marathon_results': end_result.get('marathon_results'),
            'progress_update': progress_update,
            'new_unlocks': unlocks,
            'next_recommendations': progress_service.get_next_recommendations(user_id)
        }
        
        logger.info(f"Roleplay session ended. Score: {final_score}, Unlocks: {unlocks}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error ending roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 50


@roleplay_bp.route('/progress/<user_id>', methods=['GET'])
def get_user_progress(user_id):
    """Get user's roleplay progress"""
    try:
        # Verify user can access this data
        current_user = session.get('user_id')
        if current_user != user_id and not _is_admin(current_user):
            return jsonify({'error': 'Unauthorized'}), 403
        
        progress = progress_service.get_user_roleplay_progress(user_id)
        
        return jsonify({
            'user_id': user_id,
            'progress': progress,
            'available_roleplays': progress_service.get_available_roleplays(user_id),
            'completion_stats': progress_service.get_completion_stats(user_id)
        })
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get roleplay leaderboard"""
    try:
        roleplay_id = request.args.get('roleplay_id', '1.1')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        leaderboard = progress_service.get_leaderboard(roleplay_id, limit)
        
        return jsonify({
            'roleplay_id': roleplay_id,
            'leaderboard': leaderboard,
            'total_participants': len(leaderboard)
        })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/info/<roleplay_id>', methods=['GET'])
@require_auth
def get_roleplay_info(roleplay_id):
    """Get roleplay information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get info from engine
        roleplay_info = roleplay_engine.get_roleplay_info(roleplay_id)
        
        if 'error' in roleplay_info:
            return jsonify({'error': f'Invalid roleplay ID: {roleplay_id}'}), 404
        
        return jsonify(roleplay_info)
        
    except Exception as e:
        logger.error(f"Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/available', methods=['GET'])
@require_auth
def get_available_roleplays():
    """Get list of available roleplay types"""
    try:
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
        logger.error(f"Error getting available roleplays: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/tts', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['text'])
@log_api_call
def text_to_speech():
    """Convert text to speech for Roleplay 1.1"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        logger.info(f"TTS request from user {user_id}: '{text[:50]}...'")
        
        # Handle empty text
        if not text:
            return _create_silent_audio_response()
        
        # Limit text length
        if len(text) > 2500:
            text = text[:2500]
            logger.warning("Text truncated to 2500 characters for TTS")
        
        # Generate speech
        audio_data = None
        try:
            if hasattr(elevenlabs_service, 'text_to_speech'):
                audio_stream = elevenlabs_service.text_to_speech(text)
                if audio_stream:
                    audio_data = audio_stream.getvalue()
                    logger.info(f"TTS generated successfully: {len(audio_data)} bytes")
        except Exception as tts_error:
            logger.warning(f"TTS generation failed: {tts_error}")
        
        # Use fallback if needed
        if not audio_data or len(audio_data) < 44:
            logger.info("Using fallback audio")
            audio_data = _create_emergency_audio_data(text)
        
        # Log usage
        try:
            log_user_action(user_id, 'tts_generated', {
                'text_length': len(text),
                'audio_size': len(audio_data)
            })
        except Exception as e:
            logger.warning(f"Failed to log TTS usage: {e}")
        
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
        logger.error(f"Critical TTS error: {e}")
        return _create_emergency_audio_response()


@roleplay_bp.route('/session/status', methods=['GET'])
@require_auth
def get_session_status():
    """Get current session status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'active': False, 'session': None})
        
        # Get status from engine
        session_status = roleplay_engine.get_session_status(session_id)
        
        if not session_status:
            session.pop('current_roleplay_session', None)
            return jsonify({'active': False, 'session': None})
        
        response_data = {
            'active': session_status.get('session_active', False),
            'session': {
                'session_id': session_id,
                'current_stage': session_status.get('current_stage', 'unknown'),
                'rubric_scores': session_status.get('rubric_scores', {}),
                'conversation_length': session_status.get('conversation_length', 0),
                'openai_available': session_status.get('openai_available', False)
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def _is_admin(user_id):
    """Check if user is admin"""
    try:
        profile = supabase_service.get_user_profile_by_service(user_id)
        return profile and profile.get('access_level') == 'admin'
    except:
        return False

# Health check endpoint
@roleplay_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for Roleplay 1.1 system"""
    try:
        # Check OpenAI service
        openai_status = 'unknown'
        if hasattr(roleplay_engine, 'openai_service') and roleplay_engine.openai_service:
            openai_status = 'available' if roleplay_engine.openai_service.is_available() else 'unavailable'
        
        # Check TTS service
        tts_status = 'unknown'
        if hasattr(elevenlabs_service, 'is_available'):
            tts_status = 'available' if elevenlabs_service.is_available() else 'unavailable'
        
        status_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.1',
            'services': {
                'roleplay_engine': 'running',
                'openai_service': openai_status,
                'tts_service': tts_status,
                'database': 'connected'
            },
            'active_sessions': len(getattr(roleplay_engine, 'active_sessions', {}))
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

# Test endpoint for debugging
@roleplay_bp.route('/test', methods=['GET'])
@require_auth
def test_services():
    """Test endpoint to check all services"""
    try:
        user_id = session.get('user_id')
        results = {
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Test OpenAI service
        if hasattr(roleplay_engine, 'openai_service') and roleplay_engine.openai_service:
            openai_service = roleplay_engine.openai_service
            results['openai'] = {
                'available': openai_service.is_available(),
                'status': openai_service.get_status()
            }
            
            # Test roleplay flow if available
            if openai_service.is_available():
                try:
                    test_result = openai_service.test_roleplay_flow()
                    results['openai']['test_flow'] = test_result
                except Exception as e:
                    results['openai']['test_flow'] = {'error': str(e)}
        else:
            results['openai'] = {'available': False, 'error': 'Service not initialized'}
        
        # Test TTS service
        if hasattr(elevenlabs_service, 'is_available'):
            results['tts'] = {
                'available': elevenlabs_service.is_available()
            }
            if hasattr(elevenlabs_service, 'get_status'):
                results['tts']['status'] = elevenlabs_service.get_status()
        else:
            results['tts'] = {'available': False}
        
        # Test database
        try:
            profile = supabase_service.get_user_profile_by_service(user_id)
            results['database'] = {
                'connected': True,
                'profile_found': bool(profile)
            }
        except Exception as e:
            results['database'] = {
                'connected': False,
                'error': str(e)
            }
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

# ===== HELPER FUNCTIONS =====
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