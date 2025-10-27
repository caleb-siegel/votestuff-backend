"""
Admin routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, ContactSubmission, Payout
import uuid

@api_bp.route('/admin/lists/<list_id>/approve', methods=['POST'])
def approve_list(list_id):
    """Approve a list"""
    # TODO: Add admin authentication check
    try:
        lst = List.query.get_or_404(uuid.UUID(list_id))
        lst.status = 'approved'
        from datetime import datetime
        lst.approved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'List approved',
            'list': lst.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400

@api_bp.route('/admin/lists/<list_id>/reject', methods=['POST'])
def reject_list(list_id):
    """Reject a list"""
    data = request.get_json()
    # TODO: Add admin authentication check
    
    try:
        lst = List.query.get_or_404(uuid.UUID(list_id))
        lst.status = 'rejected'
        lst.admin_notes = data.get('notes')
        db.session.commit()
        
        return jsonify({
            'message': 'List rejected',
            'list': lst.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400

@api_bp.route('/admin/contact-submissions', methods=['GET'])
def get_contact_submissions():
    """Get all contact submissions (admin)"""
    # TODO: Add admin authentication check
    submissions = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    
    return jsonify({
        'submissions': [sub.to_dict() for sub in submissions]
    })

@api_bp.route('/admin/payouts', methods=['GET'])
def get_payouts():
    """Get all payouts (admin)"""
    # TODO: Add admin authentication check
    payouts = Payout.query.order_by(Payout.created_at.desc()).all()
    
    return jsonify({
        'payouts': [payout.to_dict() for payout in payouts]
    })

