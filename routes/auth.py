"""
Authentication routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
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
        
        return jsonify({
            'message': 'User created successfully',
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
    
    # TODO: Generate JWT token
    # For now, return user info
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200

@api_bp.route('/auth/oauth', methods=['POST'])
def oauth_login():
    """OAuth login (Google, Apple, etc.)"""
    data = request.get_json()
    
    # TODO: Implement OAuth verification
    # This is a placeholder
    return jsonify({'error': 'OAuth not yet implemented'}), 501

