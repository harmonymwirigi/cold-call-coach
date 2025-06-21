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
