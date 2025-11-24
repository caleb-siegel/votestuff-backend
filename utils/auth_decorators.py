"""
Authentication decorators for protecting routes
"""

from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from models import User

def require_auth(f):
    """
    Decorator to require authentication for a route.
    Extracts user from JWT token and passes it to the route function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        try:
            # Decode JWT token - MUST use JWT_SECRET_KEY to match token generation
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            
            if not current_user.is_active:
                return jsonify({'error': 'User account is inactive'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Pass current_user to the route function
        return f(current_user, *args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin authentication for a route.
    Ensures user is authenticated AND has admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        try:
            # Decode JWT token - MUST use JWT_SECRET_KEY to match token generation
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            
            if not current_user.is_active:
                return jsonify({'error': 'User account is inactive'}), 401
            
            if not current_user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Pass current_user to the route function
        return f(current_user, *args, **kwargs)
    
    return decorated_function
