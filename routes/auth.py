"""
Authentication routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from utils.jwt import generate_token
import uuid

@api_bp.route('/auth/test', methods=['GET'])
def test_auth():
    """Test auth route"""
    return jsonify({'message': 'Auth routes working'})

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    display_name = data.get('display_name', email.split('@')[0])
    bio = data.get('bio')
    
    # Check if user exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    try:
        new_user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=generate_password_hash(password),
            display_name=display_name,
            bio=bio
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token
        token = generate_token(new_user.id, new_user.is_admin)
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': new_user.to_dict()
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    
    # Generate JWT token
    token = generate_token(user.id, user.is_admin)
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    from utils.jwt import get_current_user as _get_current_user
    
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    return jsonify({'user': user.to_dict()}), 200


@api_bp.route('/auth/oauth', methods=['POST'])
def oauth_login():
    """OAuth login (Google, Apple, etc.)"""
    from google.auth.transport import requests
    from google.oauth2 import id_token
    import os
    
    data = request.get_json()
    
    if not data or not data.get('provider') or not data.get('token'):
        return jsonify({'error': 'Provider and token required'}), 400
    
    provider = data.get('provider')
    token = data.get('token')
    
    if provider != 'google':
        return jsonify({'error': f'Provider {provider} not supported'}), 400
    
    # Verify Google token
    try:
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        if not google_client_id:
            return jsonify({'error': 'Google OAuth not configured'}), 500
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), google_client_id)
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'error': 'Invalid token issuer'}), 401
        
        # Extract user info
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture')
        
        # Check if user exists by OAuth ID or email
        user = User.query.filter(
            (User.oauth_id == google_id) | (User.email == email)
        ).first()
        
        if user:
            # Update OAuth info if needed
            if not user.oauth_provider:
                user.oauth_provider = 'google'
                user.oauth_id = google_id
            if picture and not user.profile_picture:
                user.profile_picture = picture
            if not user.display_name or user.display_name == email.split('@')[0]:
                user.display_name = name
            db.session.commit()
        else:
            # Create new user
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=None,  # OAuth users don't have passwords
                display_name=name,
                profile_picture=picture,
                oauth_provider='google',
                oauth_id=google_id
            )
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        
        # Generate JWT token
        token = generate_token(user.id, user.is_admin)
        
        return jsonify({
            'message': 'OAuth login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        # Invalid token
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': f'OAuth verification failed: {str(e)}'}), 500

