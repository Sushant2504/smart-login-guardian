"""
Authentication middleware
"""

from functools import wraps
from flask import request, jsonify
from flask_login import current_user
from datetime import datetime
from web.database.models import APIKey, db


def api_key_required(f):
    """Require valid API key for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # Validate API key
        key_obj = APIKey.query.filter_by(key=api_key, is_active=True).first()

        if not key_obj:
            return jsonify({'error': 'Invalid API key'}), 401

        # Check expiration
        if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
            return jsonify({'error': 'API key expired'}), 401

        # Update last used
        key_obj.last_used = datetime.utcnow()
        db.session.commit()

        # Add to request context
        request.api_key = key_obj
        request.api_user = key_obj.user

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)

    return decorated_function


def role_required(*roles):
    """Require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401

            if current_user.role not in roles:
                return jsonify({'error': f'Role {current_user.role} not authorized'}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
