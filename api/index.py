# ===== API/INDEX.PY (VERCEL SERVERLESS ENTRY POINT) =====
from flask import Flask, render_template, redirect, url_for, send_from_directory, make_response, request
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging for serverless
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CORS configuration
    CORS(app, supports_credentials=True)
    
    # Import and register blueprints
    try:
        from routes.auth import auth_bp
        from routes.user import user_bp
        from routes.dashboard import dashboard_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(user_bp, url_prefix='/api/user')
        app.register_blueprint(dashboard_bp)
        
        logger.info("Successfully registered auth, user, and dashboard blueprints")
        
        # Register roleplay blueprint if it exists
        try:
            from routes.roleplay import roleplay_bp
            app.register_blueprint(roleplay_bp, url_prefix='/api/roleplay')
            logger.info("Successfully registered roleplay blueprint")
        except ImportError as e:
            logger.warning(f"Roleplay blueprint not found: {e}")
        
        # Register admin blueprint if it exists
        try:
            from routes.admin import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/api/admin')
            logger.info("Successfully registered admin blueprint")
        except ImportError as e:
            logger.warning(f"Admin blueprint not found: {e}")
    
    except ImportError as e:
        logger.error(f"Failed to import required blueprints: {e}")
        # Create minimal error response
        @app.route('/api/<path:path>')
        def api_error(path):
            return {'error': 'API not properly configured', 'details': str(e)}, 500
    
    # Main routes
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
    
    @app.route('/roleplay/<int:roleplay_id>')
    def roleplay_page(roleplay_id):
        """Roleplay page"""
        # Validate roleplay ID
        if roleplay_id not in [1, 2, 3, 4, 5]:
            return redirect(url_for('dashboard_page'))
        
        return render_template('roleplay.html', roleplay_id=roleplay_id)
    
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
    
    # API Health Check
    @app.route('/api/health')
    def health_check():
        """Basic health check endpoint"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.getenv('FLASK_ENV', 'production'),
            'platform': 'vercel'
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # For API requests, return JSON
        if '/api/' in request.path:
            return {'error': 'Endpoint not found'}, 404
        # For web requests, return HTML
        try:
            return render_template('404.html'), 404
        except:
            return '<h1>404 - Page Not Found</h1>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        # For API requests, return JSON
        if '/api/' in request.path:
            return {'error': 'Internal server error', 'details': str(error)}, 500
        # For web requests, return HTML
        try:
            return render_template('500.html'), 500
        except:
            return '<h1>500 - Internal Server Error</h1>', 500
    
    # Template globals
    @app.template_global()
    def current_year():
        return datetime.now().year
    
    # Log successful startup
    logger.info("Flask application created successfully for Vercel")
    
    return app

# Create app instance
app = create_app()

# Vercel serverless function handler
def handler(event, context):
    """Serverless function handler for Vercel"""
    return app(event, context)

# For local development
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Cold Calling Coach starting on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌐 Visit: http://localhost:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )