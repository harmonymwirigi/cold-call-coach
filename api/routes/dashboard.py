# ===== FIXED API/ROUTES/DASHBOARD.PY =====
from flask import Blueprint, render_template, session, redirect, url_for, request
from utils.decorators import require_auth
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page"""
    try:
        logger.info(f"Dashboard accessed by user {session.get('user_id')}")
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return redirect(url_for('home'))

@dashboard_bp.route('/roleplay/<int:roleplay_id>')
@require_auth
def roleplay(roleplay_id):
    """Roleplay page"""
    try:
        # Validate roleplay ID
        if roleplay_id not in [1, 2, 3, 4, 5]:
            logger.warning(f"Invalid roleplay ID {roleplay_id} requested")
            return redirect(url_for('dashboard.dashboard'))  # Fixed: use dashboard.dashboard instead of dashboard_bp.dashboard
        
        logger.info(f"Roleplay {roleplay_id} accessed by user {session.get('user_id')}")
        return render_template('roleplay.html', roleplay_id=roleplay_id)
    except Exception as e:
        logger.error(f"Error rendering roleplay {roleplay_id}: {e}")
        return redirect(url_for('dashboard.dashboard'))  # Fixed: use dashboard.dashboard