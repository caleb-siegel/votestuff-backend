"""
Contact form routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, ContactSubmission
import uuid

@api_bp.route('/contact', methods=['POST'])
def submit_contact():
    """Submit contact form"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('message'):
        return jsonify({'error': 'Name, email, and message required'}), 400
    
    try:
        submission = ContactSubmission(
            id=uuid.uuid4(),
            name=data.get('name'),
            email=data.get('email'),
            subject=data.get('subject'),
            message=data.get('message')
        )
        db.session.add(submission)
        db.session.commit()
        
        return jsonify({
            'message': 'Contact submission received',
            'id': str(submission.id)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

