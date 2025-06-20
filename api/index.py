# ===== API/INDEX.PY (FIXED VERCEL HANDLER) =====
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

# Create Flask app
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
    try:
        return render_template('index.html')
    except:
        # Fallback minimal HTML
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cold Calling Coach</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                    <div class="container-fluid">
                        <a class="navbar-brand" href="/">
                            <i class="fas fa-phone-alt me-2"></i>Cold Calling Coach
                        </a>
                        <div class="navbar-nav ms-auto">
                            <a class="nav-link" href="/login">Login</a>
                            <a class="nav-link" href="/register">Register</a>
                        </div>
                    </div>
                </nav>
                
                <main class="py-5">
                    <div class="text-center">
                        <h1>🎯 Cold Calling Coach</h1>
                        <p class="lead">Master your cold calling skills with AI-powered roleplay training</p>
                        <div class="mt-4">
                            <a href="/register" class="btn btn-primary btn-lg me-3">Get Started</a>
                            <a href="/login" class="btn btn-outline-primary btn-lg">Login</a>
                        </div>
                        <div class="mt-3">
                            <a href="/api/health" class="btn btn-outline-secondary">API Health Check</a>
                        </div>
                    </div>
                </main>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''

@app.route('/register')
def register_page():
    """Registration page"""
    try:
        return render_template('register.html')
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register - Cold Calling Coach</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container py-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <h2>Create Account</h2>
                        <p>Registration system is loading...</p>
                        <a href="/" class="btn btn-outline-secondary">Back to Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login.html')
    except:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Cold Calling Coach</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container py-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <h2>Login</h2>
                        <p>Login system is loading...</p>
                        <a href="/" class="btn btn-outline-secondary">Back to Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

@app.route('/dashboard')
def dashboard_page():
    """Dashboard page"""
    try:
        return render_template('dashboard.html')
    except:
        return redirect(url_for('home'))

@app.route('/roleplay/<int:roleplay_id>')
def roleplay_page(roleplay_id):
    """Roleplay page"""
    if roleplay_id not in [1, 2, 3, 4, 5]:
        return redirect(url_for('dashboard_page'))
    
    try:
        return render_template('roleplay.html', roleplay_id=roleplay_id)
    except:
        return redirect(url_for('home'))

@app.route('/admin')
def admin_page():
    """Admin page"""
    try:
        return render_template('admin.html')
    except:
        return redirect(url_for('home'))

@app.route('/about')
def about():
    """About page"""
    try:
        return render_template('about.html')
    except:
        return '<h1>About Cold Calling Coach</h1><p>AI-powered sales training platform</p><a href="/">Home</a>'

@app.route('/pricing')
def pricing():
    """Pricing page"""
    try:
        return render_template('pricing.html')
    except:
        return '<h1>Pricing</h1><p>Pricing information coming soon</p><a href="/">Home</a>'

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests gracefully"""
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
        'platform': 'vercel',
        'message': 'Cold Calling Coach API is running successfully'
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if '/api/' in request.path:
        return {'error': 'Endpoint not found'}, 404
    return '<h1>404 - Page Not Found</h1><a href="/">Go Home</a>', 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if '/api/' in request.path:
        return {'error': 'Internal server error', 'details': str(error)}, 500
    return '<h1>500 - Internal Server Error</h1><a href="/">Go Home</a>', 500

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
# Template globals
@app.template_global()
def current_year():
    return datetime.now().year

logger.info("Flask application created successfully for Vercel")

# ===== VERCEL SERVERLESS HANDLER =====
def app_wrapper(environ, start_response):
    """WSGI wrapper for Vercel"""
    return app(environ, start_response)

# This is the entry point Vercel will use
app_wsgi = app_wrapper