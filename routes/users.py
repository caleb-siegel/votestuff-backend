"""
User routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, User, List
import uuid

@api_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        user_data = user.to_dict()
        
        # Add related data
        user_data['lists_created'] = [lst.to_dict() for lst in user.lists]
        user_data['lists_count'] = len(user.lists)
        
        return jsonify(user_data)
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400

@api_bp.route('/users/<user_id>/update', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        data = request.get_json()
        
        # Update allowed fields
        if 'display_name' in data:
            user.display_name = data.get('display_name')
        if 'bio' in data:
            user.bio = data.get('bio')
        if 'profile_picture' in data:
            user.profile_picture = data.get('profile_picture')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated',
            'user': user.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

