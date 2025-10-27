"""
JWT utility functions for authentication
"""

import jwt
from datetime import datetime, timedelta
from flask import current_app
from functools import wraps
from flask import request, jsonify
from models import User


def generate_token(user_id, is_admin=False):
    """
    Generate a JWT token for a user
    
    Args:
        user_id: The user's ID
        is_admin: Whether the user is an admin
        
    Returns:
        str: JWT token
    """
    from app import app
    
    with app.app_context():
        secret = app.config.get('JWT_SECRET_KEY', 'jwt-secret-key')
        
        payload = {
            'user_id': str(user_id),
            'is_admin': is_admin,
            'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token


def verify_token(token):
    """
    Verify a JWT token and return the user_id
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded token payload or None if invalid
    """
    from app import app
    
    try:
        with app.app_context():
            secret = app.config.get('JWT_SECRET_KEY', 'jwt-secret-key')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """
    Get the current user from the JWT token in the request
    
    Returns:
        User: The current user object or None
    """
    token = None
    
    # Try to get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    if not token:
        return None
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        return None
    
    # Get user from database
    user_id = payload.get('user_id')
    if not user_id:
        return None
    
    user = User.query.filter_by(id=user_id).first()
    return user


def token_required(f):
    """
    Decorator to protect routes that require authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(user, *args, **kwargs)
    return decorated


def admin_required(f):
    """
    Decorator to protect routes that require admin authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(user, *args, **kwargs)
    return decorated

