# ===== api/index.py (VERCEL FIXED HANDLER) =====
from flask import Flask, render_template, redirect, url_for, send_from_directory, make_response, request, session, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Configure logging for Vercel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Define the roleplay structure
ROLEPLAY_STRUCTURE = {
    '1': {
        'name': 'Opener + Early Objections',
        'description': 'Master call openings and handle early objections',
        'subtypes': {
            '1.1': {
                'name': 'Practice Mode',
                'description': 'Single call with detailed CEFR A2 coaching',
                'icon': 'user-graduate'
            },
            '1.2': {
                'name': 'Marathon Mode', 
                'description': '10 calls, need 6 to pass',
                'icon': 'running'
            },
            '1.3': {
                'name': 'Legend Mode',
                'description': '6 perfect calls in a row',
                'icon': 'crown'
            }
        }
    },
    '2': {
        'name': 'Pitch + Objections + Close',
        'description': 'Perfect your pitch and close more meetings',
        'subtypes': {
            '2.1': {
                'name': 'Practice Mode',
                'description': 'Single call with detailed coaching',
                'icon': 'user-graduate'
            },
            '2.2': {
                'name': 'Marathon Mode',
                'description': '10 calls, need 6 to pass',
                'icon': 'running'
            }
        }
    },
    '3': {
        'name': 'Warm-up Challenge',
        'description': '25 rapid-fire questions to sharpen your skills',
        'direct': True,
        'icon': 'fire'
    },
    '4': {
        'name': 'Full Cold Call Simulation', 
        'description': 'Complete end-to-end cold call practice',
        'direct': True,
        'icon': 'headset'
    },
    '5': {
        'name': 'Power Hour Challenge',
        'description': '10 consecutive calls to test your endurance',
        'direct': True,
        'icon': 'bolt'
    }
}

# Create Flask app instance
app = Flask(__name__)

# Configuration for Vercel
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS configuration
CORS(app, supports_credentials=True)

# ===== HELPER FUNCTIONS FOR ROLEPLAY ROUTING =====

def get_user_profile_safe(user_id):
    """Safely get user profile with fallback"""
    try:
        from services.supabase_client import SupabaseService
        supabase_service = SupabaseService()
        profile = supabase_service.get_user_profile_by_service(user_id)
        
        if not profile:
            logger.warning(f"No profile found for user {user_id}")
            profile = {
                'first_name': 'User',
                'prospect_job_title': 'CTO',
                'prospect_industry': 'Technology'
            }
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return {
            'first_name': 'User',
            'prospect_job_title': 'CTO',
            'prospect_industry': 'Technology'
        }

def get_roleplay_info_from_structure(roleplay_id):
    """Get roleplay info from the structure"""
    # For direct roleplays (3, 4, 5)
    if roleplay_id in ['3', '4', '5']:
        return ROLEPLAY_STRUCTURE.get(roleplay_id)
    
    # For subtypes (1.1, 1.2, etc.)
    main_id = roleplay_id.split('.')[0]
    main_info = ROLEPLAY_STRUCTURE.get(main_id)
    
    if main_info and 'subtypes' in main_info:
        subtype_info = main_info['subtypes'].get(roleplay_id)
        if subtype_info:
            # Combine main info with subtype info
            return {
                'id': roleplay_id,
                'name': subtype_info['name'],
                'description': subtype_info['description'],
                'icon': subtype_info.get('icon', 'phone'),
                'main_category': main_info['name']
            }
    
    return None

def render_roleplay_selection(main_roleplay_id, user_id):
    """Render selection page for roleplays with subtypes - FIXED"""
    try:
        # Get user profile
        profile = get_user_profile_safe(user_id)
        
        # Get roleplay info
        roleplay_info = ROLEPLAY_STRUCTURE.get(main_roleplay_id)
        if not roleplay_info:
            return redirect(url_for('dashboard_page'))
        
        logger.info(f"Rendering selection page for roleplay {main_roleplay_id}")
        
        # FIXED: Handle Roleplay 1 specifically
        if main_roleplay_id == '1':
            # Get user progress for Roleplay 1 modes
            try:
                from services.user_progress_service import UserProgressService
                progress_service = UserProgressService()
                user_progress = progress_service.get_user_roleplay_progress(user_id, ['1.1', '1.2', '1.3'])
            except Exception as e:
                logger.warning(f"Could not load user progress: {e}")
                user_progress = {}
            
            # Use the specific Roleplay 1 selection template
            return render_template(
                'roleplay/roleplay-1-selection.html',  # FIXED: Correct template path
                user_progress=user_progress,
                page_title="Roleplay 1: Choose Your Mode"
            )
        
        # For other roleplays, use generic template (when you create them later)
        else:
            return render_template(
                'roleplay/roleplay-1-selection.html',  # Generic template for other roleplays
                main_roleplay_id=main_roleplay_id,
                roleplay_info=roleplay_info,
                user_profile=profile,
                page_title=f"{roleplay_info['name']} - Choose Mode"
            )
        
    except Exception as e:
        logger.error(f"Error rendering roleplay selection: {e}")
        return redirect(url_for('dashboard_page'))


@app.route('/roleplay/<roleplay_id>')
def roleplay_page(roleplay_id):
    """Handle hierarchical roleplay routing - COMPLETE FIX"""
    try:
        # Check authentication
        if 'user_id' not in session:
            logger.warning("Unauthenticated access to roleplay page")
            return redirect(url_for('login_page'))
        
        user_id = session.get('user_id')
        logger.info(f"🎯 User {user_id} accessing roleplay {roleplay_id}")
        
        # Handle different roleplay ID formats
        if roleplay_id == '1':
            # Roleplay 1 - show selection page with modes 1.1, 1.2, 1.3
            logger.info("📋 Showing Roleplay 1 selection page")
            return render_roleplay_1_selection(user_id)
        
        elif roleplay_id == '2':
            # Roleplay 2 - show selection page with modes 2.1, 2.2
            logger.info("📋 Showing Roleplay 2 selection page")
            return render_roleplay_2_selection(user_id)
        
        elif roleplay_id in ['3', '4', '5']:
            # Roleplays 3, 4, 5 - go directly to training (no selection)
            logger.info(f"🎮 Going directly to roleplay {roleplay_id}")
            return render_specific_roleplay(roleplay_id, user_id)
        
        elif roleplay_id in ['1.1', '1.2', '1.3']:
            # Roleplay 1 specific modes - go to training
            logger.info(f"🎮 Starting Roleplay 1 mode: {roleplay_id}")
            return render_specific_roleplay(roleplay_id, user_id)
        
        elif roleplay_id in ['2.1', '2.2']:
            # Roleplay 2 specific modes - go to training
            logger.info(f"🎮 Starting Roleplay 2 mode: {roleplay_id}")
            return render_specific_roleplay(roleplay_id, user_id)
        
        else:
            # Invalid roleplay ID
            logger.warning(f"❌ Invalid roleplay ID: {roleplay_id}")
            return redirect(url_for('dashboard_page'))
            
    except Exception as e:
        logger.error(f"❌ Error in roleplay_page: {e}")
        return redirect(url_for('dashboard_page'))

def render_roleplay_1_selection(user_id):
    """Render Roleplay 1 selection page - FIXED with all variables"""
    try:
        logger.info(f"🎮 Rendering Roleplay 1 selection for user {user_id}")
        
        # Get user profile
        profile = get_user_profile_safe(user_id)
        
        # Create roleplay info for Roleplay 1
        roleplay_info = {
            'id': '1',
            'name': 'Roleplay 1: Opener & Early Objections',
            'description': 'Master call openings and handle early objections with confidence'
        }
        
        # Get user progress for Roleplay 1 modes
        try:
            from services.user_progress_service import UserProgressService
            progress_service = UserProgressService()
            user_progress = progress_service.get_user_roleplay_progress(user_id, ['1.1', '1.2', '1.3'])
            logger.info(f"📊 Loaded progress for 1.1, 1.2, 1.3: {user_progress}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load user progress: {e}")
            user_progress = {}
        
        # Use your custom template for Roleplay 1
        logger.info("📄 Rendering roleplay/roleplay-1-selection.html")
        return render_template(
            'roleplay/roleplay-1-selection.html',
            roleplay_info=roleplay_info,  # ADDED: Include roleplay_info
            user_progress=user_progress,
            user_profile=profile,
            main_roleplay_id='1',  # ADDED: Include main_roleplay_id
            page_title="Roleplay 1: Choose Your Mode"
        )
        
    except Exception as e:
        logger.error(f"❌ Error rendering Roleplay 1 selection: {e}")
        return redirect(url_for('dashboard_page'))

def render_roleplay_2_selection(user_id):
    """Render Roleplay 2 selection page - FIXED with all variables"""
    try:
        logger.info(f"🎮 Rendering Roleplay 2 selection for user {user_id}")
        
        # Get user profile
        profile = get_user_profile_safe(user_id)
        
        # Get roleplay info for Roleplay 2
        roleplay_info = {
            'id': '2',
            'name': 'Roleplay 2: Pitch + Objections + Close',
            'description': 'Perfect your pitch and close more meetings'
        }
        
        # Get user progress for Roleplay 2 modes  
        try:
            from services.user_progress_service import UserProgressService
            progress_service = UserProgressService()
            user_progress = progress_service.get_user_roleplay_progress(user_id, ['2.1', '2.2'])
            # Also get Roleplay 1 progress to check unlock status
            rp1_progress = progress_service.get_user_roleplay_progress(user_id, ['1.3'])
            user_progress.update(rp1_progress)  # Merge progress data
            logger.info(f"📊 Loaded progress for 2.1, 2.2: {user_progress}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load user progress: {e}")
            user_progress = {}
        
        # Use the generic template for Roleplay 2
        logger.info("📄 Rendering roleplay/roleplay-selection.html for Roleplay 2")
        return render_template(
            'roleplay/roleplay-selection.html',
            main_roleplay_id='2',
            roleplay_info=roleplay_info,
            user_profile=profile,
            user_progress=user_progress,
            page_title="Roleplay 2: Choose Your Mode"
        )
        
    except Exception as e:
        logger.error(f"❌ Error rendering Roleplay 2 selection: {e}")
        return redirect(url_for('dashboard_page'))

def render_specific_roleplay(roleplay_id, user_id):
    """Render specific roleplay training page - FIXED"""
    try:
        # Get user profile
        profile = get_user_profile_safe(user_id)
        
        # Check roleplay access first
        try:
            from services.user_progress_service import UserProgressService
            progress_service = UserProgressService()
            access_check = progress_service.check_roleplay_access(user_id, roleplay_id)
            
            if not access_check['allowed']:
                logger.warning(f"❌ User {user_id} doesn't have access to {roleplay_id}: {access_check['reason']}")
                # Redirect back to selection or dashboard with error message
                if roleplay_id.startswith('1.'):
                    return redirect(url_for('roleplay_page', roleplay_id='1'))
                elif roleplay_id.startswith('2.'):
                    return redirect(url_for('roleplay_page', roleplay_id='2'))
                else:
                    return redirect(url_for('dashboard_page'))
        except Exception as e:
            logger.warning(f"⚠️ Could not check access: {e}")
        
        # Get roleplay info from structure or create default
        roleplay_info = get_roleplay_info_from_structure(roleplay_id)
        
        if not roleplay_info:
            logger.warning(f"No info found for roleplay {roleplay_id}")
            # Create default info based on roleplay_id
            roleplay_names = {
                '1.1': 'Practice Mode',
                '1.2': 'Marathon Mode', 
                '1.3': 'Legend Mode',
                '2.1': 'Advanced Practice',
                '2.2': 'Advanced Marathon',
                '3': 'Warm-up Challenge',
                '4': 'Full Cold Call Simulation',
                '5': 'Power Hour Challenge'
            }
            
            roleplay_info = {
                'id': roleplay_id,
                'name': roleplay_names.get(roleplay_id, f'Roleplay {roleplay_id}'),
                'description': 'Cold calling training',
                'icon': 'phone'
            }
        
        logger.info(f"🎮 Rendering training page for {roleplay_id}")
        
        # Use the main roleplay training template
        return render_template(
            'roleplay.html',
            roleplay_id=roleplay_id,
            roleplay_info=roleplay_info,
            user_profile=profile,
            page_title=f"{roleplay_info['name']} - Cold Calling Coach"
        )
        
    except Exception as e:
        logger.error(f"❌ Error rendering specific roleplay: {e}")
        return redirect(url_for('dashboard_page'))

@app.template_global()
def get_file_version(filename):
    """Get file modification time for cache busting"""
    try:
        file_path = os.path.join(app.static_folder, filename)
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            return str(int(mtime))
        return str(int(datetime.now().timestamp()))
    except:
        return str(int(datetime.now().timestamp()))

@app.template_global()
def current_year():
    return datetime.now().year

@app.template_global()
def get_roleplay_structure():
    """Make roleplay structure available in templates"""
    return ROLEPLAY_STRUCTURE

# ===== MAIN ROUTES =====

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/register')
def register_page():
    """Registration page"""
    return render_template('register.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    """Dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/roleplay/info/<roleplay_id>', methods=['GET'])
def get_roleplay_info_api(roleplay_id):
    """Get roleplay information - FIXED VERSION"""
    try:
        # CRITICAL FIX: Handle parent categories first
        original_id = roleplay_id
        if roleplay_id == '1':
            roleplay_id = '1.1'
        elif roleplay_id == '2':
            roleplay_id = '2.1'
        
        logger.info(f"API request for roleplay info: {original_id} -> {roleplay_id}")
        
        # Simple roleplay info
        roleplay_configs = {
            '1.1': {
                'id': '1.1', 
                'name': 'Practice Mode', 
                'description': 'Single call with detailed coaching', 
                'icon': 'user-graduate', 
                'available': True
            },
            '1.2': {
                'id': '1.2', 
                'name': 'Marathon Mode', 
                'description': '10 calls, need 6 to pass', 
                'icon': 'running', 
                'available': True
            },
            '1.3': {
                'id': '1.3', 
                'name': 'Legend Mode', 
                'description': '6 perfect calls in a row', 
                'icon': 'crown', 
                'available': False
            },
            '2.1': {
                'id': '2.1', 
                'name': 'Pitch Practice', 
                'description': 'Advanced pitch training', 
                'icon': 'bullhorn', 
                'available': False
            },
            '2.2': {
                'id': '2.2', 
                'name': 'Pitch Marathon', 
                'description': '10 advanced calls', 
                'icon': 'running', 
                'available': False
            },
            '3': {
                'id': '3', 
                'name': 'Warm-up Challenge', 
                'description': '25 rapid-fire questions', 
                'icon': 'fire', 
                'available': True
            },
            '4': {
                'id': '4', 
                'name': 'Full Cold Call', 
                'description': 'Complete simulation', 
                'icon': 'headset', 
                'available': True
            },
            '5': {
                'id': '5', 
                'name': 'Power Hour', 
                'description': '10 consecutive calls', 
                'icon': 'bolt', 
                'available': True
            }
        }
        
        if roleplay_id not in roleplay_configs:
            logger.warning(f"Invalid roleplay ID: {roleplay_id}")
            return jsonify({'error': f'Invalid roleplay ID: {roleplay_id}'}), 404
        
        result = roleplay_configs[roleplay_id]
        logger.info(f"Returning roleplay info for {original_id}: {result['name']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting roleplay info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test/simple-start', methods=['POST'])
def test_simple_start():
    """Emergency test endpoint for Vercel"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id', 'test_user')
        
        # Create minimal session
        session_id = f"test_{user_id}_{int(datetime.now().timestamp())}"
        initial_response = "Hello, this is Alex speaking. How can I help you?"
        
        # Store in session for testing
        session['current_roleplay_session'] = session_id
        
        logger.info(f"Test session created: {session_id}")
        
        return jsonify({
            'message': 'Test session started',
            'session_id': session_id,
            'roleplay_id': data.get('roleplay_id', '1.1'),
            'mode': data.get('mode', 'practice'),
            'initial_response': initial_response,
            'tts_available': False
        })
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/roleplay')
def roleplay_default():
    """Default roleplay route - redirect to roleplay 1 selection"""
    return redirect(url_for('roleplay_page', roleplay_id='1'))

@app.route('/training')
@app.route('/training/<roleplay_id>')
def training_redirect(roleplay_id='1'):
    """Redirect old training URLs to roleplay"""
    return redirect(url_for('roleplay_page', roleplay_id=roleplay_id))

# ===== OTHER PAGES =====

@app.route('/admin')
def admin_page():
    """Admin page"""
    return render_template('admin.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests gracefully"""
    try:
        return send_from_directory(app.static_folder, 'favicon.ico')
    except:
        # Create a simple response if favicon doesn't exist
        response = make_response('')
        response.headers['Content-Type'] = 'image/x-icon'
        response.headers['Content-Length'] = '0'
        return response

@app.route('/api/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.getenv('VERCEL_ENV', 'development'),
        'roleplay_structure': {
            'main_categories': list(ROLEPLAY_STRUCTURE.keys()),
            'available_specific_ids': ['1.1', '1.2', '1.3', '2.1', '2.2', '3', '4', '5']
        }
    })

@app.route('/api/roleplay/structure', methods=['GET'])
def get_roleplay_structure_api():
    """Get available roleplay structure"""
    return jsonify({
        'roleplay_structure': ROLEPLAY_STRUCTURE,
        'available_specific_ids': ['1.1', '1.2', '1.3', '2.1', '2.2', '3', '4', '5'],
        'main_categories': ['1', '2', '3', '4', '5']
    })

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    # For API requests, return JSON
    if '/api/' in request.path:
        return jsonify({'error': 'Endpoint not found'}), 404
    # For web requests, return HTML
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    # For API requests, return JSON
    if '/api/' in request.path:
        return jsonify({'error': 'Internal server error'}), 500
    # For web requests, return HTML
    return render_template('500.html'), 500

# ===== BLUEPRINT REGISTRATION =====
# Import and register blueprints after app creation
try:
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.dashboard import dashboard_bp
    from routes.roleplay import roleplay_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(roleplay_bp, url_prefix='/api/roleplay')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(dashboard_bp)
    
    logger.info("Successfully registered auth, user, and dashboard blueprints")
    
    # Register debug routes in development
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG') == 'true':
        try:
            from routes.debug import debug_bp
            app.register_blueprint(debug_bp, url_prefix='/api/debug')
            logger.info("Successfully registered debug blueprint")
        except ImportError:
            logger.warning("Debug blueprint not found")

except ImportError as e:
    logger.error(f"Failed to import required blueprints: {e}")
    # Create minimal error response
    @app.route('/api/<path:path>')
    def api_error(path):
        return {'error': 'API not properly configured'}, 500

# Log successful startup
logger.info("Flask application created successfully for Vercel deployment")
logger.info(f"Available roleplay routes: {list(ROLEPLAY_STRUCTURE.keys())}")

# ===== VERCEL EXPORT =====
# For Vercel deployment, just export the app directly
# Vercel will handle the WSGI interface automatically

# For local development only
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    print(f"🚀 Cold Calling Coach starting on port {port}")
    print(f"🌐 Visit: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)