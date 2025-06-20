# ===== ENHANCED API ROUTES - MARATHON MODE SUPPORT =====

from flask import Blueprint, request, jsonify, session, Response
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Import services with error handling
try:
    from services.supabase_client import SupabaseService
    from services.elevenlabs_service import ElevenLabsService  
    from services.roleplay_engine import RoleplayEngine
except ImportError as e:
    logger.error(f"Service import error: {e}")
    # Create placeholder classes
    class SupabaseService:
        def __init__(self): pass
        def get_user_profile_by_service(self, user_id): return {}
        def get_service_client(self): return self
        def table(self, name): return self
        def insert(self, data): return self
        def execute(self): return {'data': []}
        def update_user_profile_by_service(self, user_id, updates): pass
    
    class ElevenLabsService:
        def __init__(self): pass
        def text_to_speech(self, text, settings=None): return None
        def is_available(self): return False
    
    class RoleplayEngine:
        def __init__(self): pass

# Import utilities with error handling  
try:
    from utils.decorators import require_auth, check_usage_limits, validate_json_input, log_api_call
    from utils.helpers import log_user_action, format_duration
    from utils.constants import ROLEPLAY_CONFIG
except ImportError as e:
    logger.error(f"Utils import error: {e}")
    # Create placeholder decorators
    def require_auth(f): return f
    def check_usage_limits(f): return f
    def validate_json_input(**kwargs): return lambda f: f
    def log_api_call(f): return f
    def log_user_action(*args, **kwargs): pass
    def format_duration(minutes): return f"{minutes} min"
    ROLEPLAY_CONFIG = {
        1: {
            'id': 1, 
            'name': 'Roleplay Training', 
            'description': 'Cold calling practice with AI evaluation',
            'modes': ['practice', 'marathon', 'legend']
        }
    }

# Create blueprint
roleplay_bp = Blueprint('roleplay', __name__, url_prefix='/api/roleplay')

# Initialize services
try:
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()
    logger.info("Roleplay services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing services: {e}")
    supabase_service = SupabaseService()
    elevenlabs_service = ElevenLabsService()
    roleplay_engine = RoleplayEngine()

@roleplay_bp.route('/start', methods=['POST'])
@require_auth
@check_usage_limits
@validate_json_input(required_fields=['roleplay_id', 'mode'])
@log_api_call
def start_roleplay():
    """Start a new Roleplay session (Practice 1.1, Marathon 1.2, or Legend)"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        roleplay_id = data.get('roleplay_id')
        mode = data.get('mode', 'practice')
        
        logger.info(f"Starting Roleplay session: roleplay_id={roleplay_id}, mode={mode}, user={user_id}")
        
        # Validate roleplay ID and mode
        if roleplay_id not in ROLEPLAY_CONFIG:
            return jsonify({'error': f'Invalid roleplay ID: {roleplay_id}'}), 400
        
        valid_modes = ['practice', 'marathon', 'legend']
        if mode not in valid_modes:
            return jsonify({'error': f'Invalid mode: {mode}. Valid modes: {valid_modes}'}), 400
        
        # Check user access for Marathon/Legend modes
        access_check = _check_mode_access(user_id, mode)
        if not access_check['allowed']:
            return jsonify({'error': access_check['message']}), 403
        
        # Get user profile
        try:
            profile = supabase_service.get_user_profile_by_service(user_id)
            if not profile:
                logger.warning(f"No profile found for user {user_id}, using defaults")
                profile = {
                    'first_name': 'User',
                    'prospect_job_title': 'CTO',
                    'prospect_industry': 'Technology',
                    'access_level': 'limited_trial'
                }
        except Exception as e:
            logger.warning(f"Error getting user profile: {e}, using defaults")
            profile = {
                'first_name': 'User',
                'prospect_job_title': 'CTO', 
                'prospect_industry': 'Technology',
                'access_level': 'limited_trial'
            }
        
        # Prepare user context with mode-specific info
        user_context = {
            'first_name': profile.get('first_name', 'User'),
            'prospect_job_title': profile.get('prospect_job_title', 'CTO'),
            'prospect_industry': profile.get('prospect_industry', 'Technology'),
            'custom_ai_notes': profile.get('custom_ai_notes', ''),
            'access_level': profile.get('access_level', 'limited_trial'),
            'roleplay_version': '1.1' if mode == 'practice' else '1.2',
            'mode': mode
        }
        
        logger.info(f"User context: {user_context}")
        
        # Create roleplay session
        session_result = roleplay_engine.create_session(
            user_id=user_id,
            roleplay_id=roleplay_id,
            mode=mode,
            user_context=user_context
        )
        
        if not session_result.get('success'):
            error_msg = session_result.get('error', 'Failed to create session')
            logger.error(f"Session creation failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Store session ID
        session['current_roleplay_session'] = session_result['session_id']
        
        # Log action with mode-specific details
        action_data = {
            'roleplay_id': roleplay_id,
            'mode': mode,
            'session_id': session_result['session_id']
        }
        
        if mode in ['marathon', 'legend']:
            call_info = session_result.get('call_info', {})
            action_data.update({
                'max_calls': call_info.get('max_calls', 1),
                'pass_threshold': call_info.get('pass_threshold', 1)
            })
        
        try:
            log_user_action(user_id, f'roleplay_{mode}_started', action_data)
        except Exception as e:
            logger.warning(f"Failed to log action: {e}")
        
        # Return response with mode-specific info
        response_data = {
            'message': f'Roleplay {mode} session started successfully',
            'session_id': session_result['session_id'],
            'roleplay_id': roleplay_id,
            'mode': mode,
            'initial_response': session_result.get('initial_response', 'Hello?'),
            'user_context': user_context,
            'tts_available': elevenlabs_service.is_available() if hasattr(elevenlabs_service, 'is_available') else False
        }
        
        # Add call info for Marathon/Legend modes
        if mode in ['marathon', 'legend']:
            response_data['call_info'] = session_result.get('call_info', {
                'current_call': 1,
                'max_calls': 10 if mode == 'marathon' else 6,
                'pass_threshold': 6
            })
        
        logger.info(f"Roleplay {mode} session started: {session_result['session_id']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error starting roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/respond', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['user_input'])
@log_api_call
def handle_user_response():
    """Handle user input during any roleplay mode"""
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
        
        # Determine response type based on results
        response_type = _determine_response_type(response_result)
        
        # Log interaction with response type info
        try:
            log_user_action(user_id, 'roleplay_interaction', {
                'session_id': session_id,
                'user_input_length': len(user_input),
                'ai_response_length': len(response_result.get('ai_response', '')),
                'response_type': response_type,
                'call_info': response_result.get('call_info', {}),
                'evaluation': response_result.get('evaluation', {}) if response_result.get('evaluation') else None
            })
        except Exception as e:
            logger.warning(f"Failed to log interaction: {e}")
        
        # Build response based on type
        response_data = _build_response_data(response_result, response_type)
        
        logger.info(f"Response sent: type={response_type}, continues={response_data.get('call_continues', False)}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error handling user response: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/tts', methods=['POST'])
@require_auth
@validate_json_input(required_fields=['text'])
@log_api_call
def text_to_speech():
    """Convert text to speech for any roleplay mode"""
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

@roleplay_bp.route('/end', methods=['POST'])
@require_auth
@log_api_call
def end_roleplay():
    """End roleplay session and provide coaching (all modes)"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        forced_end = data.get('forced_end', False)
        
        # Get session ID
        session_id = session.get('current_roleplay_session')
        if not session_id:
            return jsonify({'error': 'No active roleplay session found'}), 400
        
        logger.info(f"Ending roleplay session {session_id} for user {user_id}")
        
        # End session
        end_result = roleplay_engine.end_session(session_id, forced_end)
        
        if not end_result.get('success'):
            error_msg = end_result.get('error', 'Failed to end session')
            logger.error(f"Session ending failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Save session to database
        session_data = end_result.get('session_data', {})
        mode = session_data.get('mode', 'practice')
        
        # Prepare session record
        voice_session_record = _prepare_session_record(user_id, end_result, session_data)
        
        try:
            supabase_service.get_service_client().table('voice_sessions').insert(voice_session_record).execute()
            logger.info("Session saved to database")
        except Exception as e:
            logger.warning(f"Failed to save session to database: {e}")
        
        # Update user usage and Marathon/Legend progress
        try:
            _update_user_usage_and_progress(user_id, end_result, mode)
        except Exception as e:
            logger.warning(f"Failed to update user usage/progress: {e}")
        
        # Clear session
        session.pop('current_roleplay_session', None)
        
        # Log completion with mode-specific data
        completion_data = {
            'session_id': session_id,
            'mode': mode,
            'duration_minutes': end_result.get('duration_minutes', 1),
            'success': end_result.get('session_success', False),
            'score': end_result.get('overall_score', 50)
        }
        
        # Add Marathon/Legend specific completion data
        if mode in ['marathon', 'legend']:
            final_stats = end_result.get('final_stats', {})
            completion_data.update({
                'calls_passed': final_stats.get('calls_passed', 0),
                'calls_failed': final_stats.get('calls_failed', 0),
                'total_calls': final_stats.get('total_calls', 1),
                'pass_rate': final_stats.get('pass_rate', 0)
            })
        
        try:
            log_user_action(user_id, f'roleplay_{mode}_completed', completion_data)
        except Exception as e:
            logger.warning(f"Failed to log completion: {e}")
        
        # Build response based on mode
        response_data = _build_end_response(end_result, mode)
        
        logger.info(f"Roleplay {mode} session ended successfully. Score: {response_data['overall_score']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error ending roleplay: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/session/status', methods=['GET'])
@require_auth
def get_session_status():
    """Get current session status (all modes)"""
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
                'mode': session_status.get('mode', 'practice'),
                'current_stage': session_status.get('current_stage', 'unknown'),
                'rubric_scores': session_status.get('rubric_scores', {}),
                'conversation_length': session_status.get('conversation_length', 0),
                'openai_available': session_status.get('openai_available', False),
                'turn_count': session_status.get('turn_count', 0)
            }
        }
        
        # Add Marathon/Legend specific status
        if session_status.get('mode') in ['marathon', 'legend']:
            marathon_status = session_status.get('marathon_status', {})
            response_data['session'].update({
                'current_call': marathon_status.get('current_call', 1),
                'max_calls': marathon_status.get('max_calls', 1),
                'calls_passed': marathon_status.get('calls_passed', 0),
                'calls_failed': marathon_status.get('calls_failed', 0),
                'run_complete': marathon_status.get('run_complete', False)
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/info/<int:roleplay_id>', methods=['GET'])
@require_auth
def get_roleplay_info(roleplay_id):
    """Get roleplay information including Marathon/Legend details"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if roleplay_id not in ROLEPLAY_CONFIG:
            return jsonify({'error': 'Invalid roleplay ID'}), 404
        
        # Get configuration
        config = ROLEPLAY_CONFIG[roleplay_id].copy()
        
        # Add enhanced info for all modes
        if roleplay_id == 1:
            config.update({
                'roleplay_versions': ['1.1', '1.2'],
                'enhanced_description': 'Cold calling training with AI evaluation, multiple modes available.',
                'modes': {
                    'practice': {
                        'name': 'Practice Mode (1.1)',
                        'description': 'Single call with real-time coaching',
                        'calls': 1,
                        'real_time_feedback': True,
                        'coaching_level': 'CEFR A2'
                    },
                    'marathon': {
                        'name': 'Marathon Mode (1.2)', 
                        'description': '10 calls, need 6 to pass',
                        'calls': 10,
                        'pass_threshold': 6,
                        'real_time_feedback': False,
                        'coaching_level': 'CEFR A2',
                        'unlocks': 'Legend Mode + Modules 2.1 & 2.2'
                    },
                    'legend': {
                        'name': 'Legend Mode (1.2)',
                        'description': '6 perfect calls (sudden death)',
                        'calls': 6,
                        'pass_threshold': 6,
                        'sudden_death': True,
                        'real_time_feedback': False,
                        'coaching_level': 'CEFR A2',
                        'requires': 'Marathon pass to unlock'
                    }
                },
                'features': {
                    'ai_evaluation': True,
                    'dynamic_scoring': True,
                    'realistic_conversations': True,
                    'silence_monitoring': True,
                    'cefr_a2_coaching': True,
                    'multi_call_training': True,
                    'objection_variety': True
                },
                'stages': [
                    'Phone Pickup',
                    'Opener Evaluation', 
                    'Early Objection',
                    'Objection Handling',
                    'Mini-Pitch',
                    'Soft Discovery'
                ]
            })
        
        # Add user access info
        try:
            user_access = _get_user_mode_access(user_id)
            config['user_access'] = user_access
        except Exception as e:
            logger.warning(f"Failed to get user access info: {e}")
            config['user_access'] = {
                'practice': True,
                'marathon': True,
                'legend': False,
                'legend_attempts_remaining': 0
            }
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ===== NEW MARATHON/LEGEND SPECIFIC ENDPOINTS =====

@roleplay_bp.route('/marathon/stats', methods=['GET'])
@require_auth  
def get_marathon_stats():
    """Get user's Marathon/Legend statistics"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get Marathon/Legend session history
        try:
            # Query voice_sessions for Marathon/Legend runs
            result = supabase_service.get_service_client().table('voice_sessions').select('*').eq('user_id', user_id).in_('mode', ['marathon', 'legend']).order('ended_at', desc=True).limit(20).execute()
            
            sessions = result.data if result.data else []
            
            # Calculate statistics
            stats = _calculate_marathon_stats(sessions)
            
            return jsonify({
                'success': True,
                'stats': stats,
                'recent_sessions': sessions[:10]  # Last 10 sessions
            })
            
        except Exception as e:
            logger.warning(f"Failed to get Marathon stats from database: {e}")
            return jsonify({
                'success': True,
                'stats': _get_default_marathon_stats(),
                'recent_sessions': []
            })
        
    except Exception as e:
        logger.error(f"Error getting Marathon stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@roleplay_bp.route('/marathon/leaderboard', methods=['GET'])
@require_auth
def get_marathon_leaderboard():
    """Get Marathon/Legend leaderboard"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        try:
            # Get top Marathon performers (anonymized)
            marathon_result = supabase_service.get_service_client().table('voice_sessions').select('score, session_data').eq('mode', 'marathon').eq('success', True).order('score', desc=True).limit(10).execute()
            
            # Get top Legend performers (anonymized)  
            legend_result = supabase_service.get_service_client().table('voice_sessions').select('score, session_data').eq('mode', 'legend').eq('success', True).order('score', desc=True).limit(10).execute()
            
            marathon_leaders = _anonymize_leaderboard(marathon_result.data if marathon_result.data else [])
            legend_leaders = _anonymize_leaderboard(legend_result.data if legend_result.data else [])
            
            return jsonify({
                'success': True,
                'marathon_leaderboard': marathon_leaders,
                'legend_leaderboard': legend_leaders
            })
            
        except Exception as e:
            logger.warning(f"Failed to get leaderboard from database: {e}")
            return jsonify({
                'success': True,
                'marathon_leaderboard': [],
                'legend_leaderboard': []
            })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@roleplay_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for roleplay system (all modes)"""
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
            'versions': ['1.1', '1.2'],
            'modes': ['practice', 'marathon', 'legend'],
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

# ===== HELPER FUNCTIONS =====

def _check_mode_access(user_id: str, mode: str) -> Dict[str, Any]:
    """Check if user has access to the requested mode"""
    if mode == 'practice':
        return {'allowed': True, 'message': 'Practice mode available to all users'}
    
    if mode == 'marathon':
        # Marathon is generally available, but check usage limits
        return {'allowed': True, 'message': 'Marathon mode available'}
    
    if mode == 'legend':
        # Legend requires Marathon pass to unlock
        try:
            profile = supabase_service.get_user_profile_by_service(user_id)
            legend_unlocked = profile.get('legend_mode_unlocked', False) if profile else False
            
            if legend_unlocked:
                return {'allowed': True, 'message': 'Legend mode unlocked'}
            else:
                return {'allowed': False, 'message': 'Legend mode requires Marathon pass to unlock'}
        except Exception as e:
            logger.warning(f"Failed to check Legend access: {e}")
            return {'allowed': False, 'message': 'Unable to verify Legend mode access'}
    
    return {'allowed': False, 'message': f'Unknown mode: {mode}'}

def _get_user_mode_access(user_id: str) -> Dict[str, Any]:
    """Get user's access status for all modes"""
    try:
        profile = supabase_service.get_user_profile_by_service(user_id)
        
        if not profile:
            return {
                'practice': True,
                'marathon': True, 
                'legend': False,
                'legend_attempts_remaining': 0
            }
        
        # Check Legend unlock status
        legend_unlocked = profile.get('legend_mode_unlocked', False)
        legend_attempts = profile.get('legend_attempts_remaining', 0)
        
        return {
            'practice': True,
            'marathon': True,
            'legend': legend_unlocked,
            'legend_attempts_remaining': legend_attempts
        }
        
    except Exception as e:
        logger.warning(f"Failed to get user mode access: {e}")
        return {
            'practice': True,
            'marathon': True,
            'legend': False,
            'legend_attempts_remaining': 0
        }

def _determine_response_type(response_result: Dict) -> str:
    """Determine the type of response based on result data"""
    if response_result.get('run_complete'):
        if response_result.get('sudden_death'):
            return 'legend_failed'
        elif response_result.get('perfect_run'):
            return 'legend_perfect'
        else:
            return 'marathon_complete'
    elif response_result.get('next_call'):
        return 'next_call'
    elif not response_result.get('call_continues'):
        return 'call_ended'
    else:
        return 'continue_call'

def _build_response_data(response_result: Dict, response_type: str) -> Dict[str, Any]:
    """Build response data based on response type"""
    base_data = {
        'success': True,
        'ai_response': response_result.get('ai_response', ''),
        'call_continues': response_result.get('call_continues', False),
        'session_state': response_result.get('session_state', 'unknown')
    }
    
    # Add evaluation for Practice mode only
    if response_result.get('evaluation') and response_type == 'continue_call':
        base_data['evaluation'] = response_result['evaluation']
    
    # Add call info for Marathon/Legend modes
    if response_result.get('call_info'):
        base_data['call_info'] = response_result['call_info']
    
    # Add specific fields based on response type
    if response_type in ['marathon_complete', 'legend_failed', 'legend_perfect']:
        base_data.update({
            'run_complete': True,
            'run_success': response_result.get('run_success', False),
            'final_stats': response_result.get('final_stats', {}),
            'coaching': response_result.get('coaching', {}),
            'overall_score': response_result.get('overall_score', 50)
        })
        
        if response_type == 'legend_failed':
            base_data['sudden_death'] = True
        elif response_type == 'legend_perfect':
            base_data['perfect_run'] = True
    
    elif response_type == 'next_call':
        base_data['next_call'] = True
    
    return base_data

def _prepare_session_record(user_id: str, end_result: Dict, session_data: Dict) -> Dict[str, Any]:
    """Prepare session record for database"""
    mode = session_data.get('mode', 'practice')
    
    base_record = {
        'user_id': user_id,
        'roleplay_id': session_data.get('roleplay_id', 1),
        'mode': mode,
        'started_at': session_data.get('started_at', datetime.now(timezone.utc).isoformat()),
        'ended_at': session_data.get('ended_at', datetime.now(timezone.utc).isoformat()),
        'duration_minutes': end_result.get('duration_minutes', 1),
        'success': end_result.get('session_success', False),
        'score': end_result.get('overall_score', 50),
        'feedback_data': end_result.get('coaching', {}),
        'session_data': session_data
    }
    
    # Add Marathon/Legend specific fields
    if mode in ['marathon', 'legend']:
        final_stats = end_result.get('final_stats', {})
        base_record.update({
            'calls_passed': final_stats.get('calls_passed', 0),
            'calls_failed': final_stats.get('calls_failed', 0),
            'total_calls': final_stats.get('total_calls', 1),
            'pass_rate': final_stats.get('pass_rate', 0)
        })
    
    return base_record

def _update_user_usage_and_progress(user_id: str, end_result: Dict, mode: str):
    """Update user's usage statistics and Marathon/Legend progress"""
    try:
        duration_minutes = end_result.get('duration_minutes', 1)
        session_success = end_result.get('session_success', False)
        
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            return
        
        # Update basic usage
        new_monthly = (profile.get('monthly_usage_minutes') or 0) + duration_minutes
        new_lifetime = (profile.get('lifetime_usage_minutes') or 0) + duration_minutes
        
        updates = {
            'monthly_usage_minutes': new_monthly,
            'lifetime_usage_minutes': new_lifetime
        }
        
        # Update Marathon/Legend progress
        if mode == 'marathon' and session_success:
            # Marathon pass unlocks Legend mode
            updates['legend_mode_unlocked'] = True
            updates['legend_attempts_remaining'] = 1
            logger.info(f"User {user_id} unlocked Legend mode via Marathon pass")
        
        elif mode == 'legend':
            if session_success:
                # Legend success - could add special achievements
                updates['legend_completions'] = (profile.get('legend_completions') or 0) + 1
                logger.info(f"User {user_id} completed Legend mode!")
            
            # Use up Legend attempt
            current_attempts = profile.get('legend_attempts_remaining', 0)
            updates['legend_attempts_remaining'] = max(0, current_attempts - 1)
        
        supabase_service.update_user_profile_by_service(user_id, updates)
        logger.info(f"Updated usage and progress for user {user_id}: +{duration_minutes} minutes, mode={mode}, success={session_success}")
        
    except Exception as e:
        logger.error(f"Error updating user usage and progress: {e}")

def _build_end_response(end_result: Dict, mode: str) -> Dict[str, Any]:
    """Build end response based on mode"""
    base_response = {
        'message': f'{mode.capitalize()} session ended successfully',
        'duration_minutes': end_result.get('duration_minutes', 1),
        'session_success': end_result.get('session_success', False),
        'coaching': end_result.get('coaching', {}),
        'overall_score': end_result.get('overall_score', 50),
        'mode': mode,
        'formatted_duration': format_duration(end_result.get('duration_minutes', 1))
    }
    
    # Add Marathon/Legend specific data
    if mode in ['marathon', 'legend']:
        final_stats = end_result.get('final_stats')
        if final_stats:
            base_response['final_stats'] = final_stats
            
            # Add completion message based on results
            calls_passed = final_stats.get('calls_passed', 0)
            total_calls = final_stats.get('total_calls', 1)
            
            if mode == 'marathon':
                if calls_passed >= 6:
                    base_response['completion_message'] = f"Marathon PASSED! {calls_passed}/{total_calls} calls passed. Legend Mode unlocked!"
                else:
                    base_response['completion_message'] = f"Marathon complete: {calls_passed}/{total_calls} calls passed. Keep practicing!"
            else:  # legend
                if calls_passed == total_calls:
                    base_response['completion_message'] = f"LEGENDARY! Perfect {calls_passed}/{total_calls} run - very few achieve this!"
                else:
                    base_response['completion_message'] = f"Legend attempt: {calls_passed}/{total_calls} calls passed. Pass Marathon again for another shot!"
    else:
        base_response['completion_message'] = f"Practice session complete! Score: {base_response['overall_score']}/100"
    
    return base_response

def _calculate_marathon_stats(sessions: List[Dict]) -> Dict[str, Any]:
    """Calculate Marathon/Legend statistics from session history"""
    marathon_sessions = [s for s in sessions if s.get('mode') == 'marathon']
    legend_sessions = [s for s in sessions if s.get('mode') == 'legend']
    
    # Marathon stats
    marathon_attempts = len(marathon_sessions)
    marathon_passes = len([s for s in marathon_sessions if s.get('success')])
    marathon_best_score = max([s.get('score', 0) for s in marathon_sessions], default=0)
    
    # Legend stats
    legend_attempts = len(legend_sessions)
    legend_completions = len([s for s in legend_sessions if s.get('success')])
    legend_best_score = max([s.get('score', 0) for s in legend_sessions], default=0)
    
    return {
        'marathon': {
            'attempts': marathon_attempts,
            'passes': marathon_passes,
            'pass_rate': (marathon_passes / marathon_attempts * 100) if marathon_attempts > 0 else 0,
            'best_score': marathon_best_score
        },
        'legend': {
            'attempts': legend_attempts,
            'completions': legend_completions,
            'completion_rate': (legend_completions / legend_attempts * 100) if legend_attempts > 0 else 0,
            'best_score': legend_best_score
        },
        'total_sessions': len(sessions),
        'last_session': sessions[0].get('ended_at') if sessions else None
    }

def _get_default_marathon_stats() -> Dict[str, Any]:
    """Get default Marathon stats when database is unavailable"""
    return {
        'marathon': {
            'attempts': 0,
            'passes': 0,
            'pass_rate': 0,
            'best_score': 0
        },
        'legend': {
            'attempts': 0,
            'completions': 0,
            'completion_rate': 0,
            'best_score': 0
        },
        'total_sessions': 0,
        'last_session': None
    }

def _anonymize_leaderboard(sessions: List[Dict]) -> List[Dict]:
    """Anonymize leaderboard data for privacy"""
    leaderboard = []
    
    for i, session in enumerate(sessions):
        entry = {
            'rank': i + 1,
            'score': session.get('score', 0),
            'anonymous_id': f"Player_{i+1:03d}",
            'date': session.get('ended_at', '')[:10] if session.get('ended_at') else ''
        }
        
        # Add mode-specific stats if available
        session_data = session.get('session_data', {})
        if session_data:
            entry['calls_passed'] = session_data.get('calls_passed', 0)
            entry['total_calls'] = session_data.get('current_call', 1)
        
        leaderboard.append(entry)
    
    return leaderboard

# Include all other helper functions from the original implementation...
# (_create_silent_audio_response, _create_emergency_audio_data, etc.)

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