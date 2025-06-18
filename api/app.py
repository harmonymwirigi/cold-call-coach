# ===== API/APP.PY (COMPLETELY FIXED) =====
from flask import Flask, render_template, redirect, url_for, send_from_directory, make_response,request
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Configure logging
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
            'environment': os.getenv('FLASK_ENV', 'development')
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # For API requests, return JSON
        if '/api/' in request.path:
            return {'error': 'Endpoint not found'}, 404
        # For web requests, return HTML
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        # For API requests, return JSON
        if '/api/' in request.path:
            return {'error': 'Internal server error'}, 500
        # For web requests, return HTML
        return render_template('500.html'), 500
    
    # Template globals
    @app.template_global()
    def current_year():
        return datetime.now().year
    
    # Log successful startup
    logger.info("Flask application created successfully")
    
    return app

# Create app instance
app = create_app()
# Create app instance
app = create_app()

# For Vercel deployment
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

# Export for Vercel
def handler(event, context):
    return app(event, context)