"""
User routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, User, List, Payout, Conversion
from sqlalchemy import desc, or_
from datetime import datetime
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

@api_bp.route('/users/<user_id>/cashback/stats', methods=['GET'])
def get_cashback_stats(user_id):
    """Get user cashback statistics"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        stats = user.get_cashback_stats()
        
        return jsonify(stats)
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400

@api_bp.route('/users/<user_id>/cashback/transactions', methods=['GET'])
def get_cashback_transactions(user_id):
    """Get user cashback transaction history (from conversions they made)"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        # Get query parameters
        status = request.args.get('status')  # Filter by conversion status: pending, approved, paid, cancelled
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query - get conversions where this user purchased OR clicked (for cashback)
        # We check both purchaser_id and payouts to find all relevant conversions
        
        # Get conversions where user is purchaser
        purchaser_conversions = Conversion.query.filter_by(purchaser_id=user.id)
        
        # Get conversions where user has cashback payouts (they clicked)
        cashback_payouts = Payout.query.filter_by(
            user_id=user.id,
            payout_type='cashback'
        ).all()
        cashback_conversion_ids = [p.conversion_id for p in cashback_payouts if p.conversion_id]
        
        # Combine both queries
        if cashback_conversion_ids:
            query = Conversion.query.filter(
                or_(
                    Conversion.purchaser_id == user.id,
                    Conversion.id.in_(cashback_conversion_ids)
                )
            )
        else:
            query = purchaser_conversions
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by created_at descending (most recent first)
        query = query.order_by(desc(Conversion.created_at))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        conversions = query.limit(limit).offset(offset).all()
        
        # Get related payouts for each conversion
        conversion_data = []
        for conv in conversions:
            conv_dict = conv.to_dict()
            
            # Get the cashback payout for this conversion
            cashback_payout = Payout.query.filter_by(
                conversion_id=conv.id,
                payout_type='cashback',
                user_id=user.id
            ).first()
            
            if cashback_payout:
                conv_dict['cashback_payout'] = cashback_payout.to_dict()
            
            conversion_data.append(conv_dict)
        
        return jsonify({
            'transactions': conversion_data,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>/cashback/transactions/<transaction_id>', methods=['GET'])
def get_cashback_transaction(user_id, transaction_id):
    """Get single cashback transaction details (conversion)"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        conversion_id = uuid.UUID(transaction_id)
        
        # Check if user is purchaser or has cashback payout for this conversion
        conversion = Conversion.query.filter(
            (Conversion.id == conversion_id) & (
                (Conversion.purchaser_id == user.id) |
                (Conversion.id.in_(
                    db.session.query(Payout.conversion_id).filter_by(
                        user_id=user.id,
                        payout_type='cashback'
                    )
                ))
            )
        ).first_or_404()
        
        conv_dict = conversion.to_dict()
        
        # Get the cashback payout for this conversion
        cashback_payout = Payout.query.filter_by(
            conversion_id=conversion.id,
            payout_type='cashback',
            user_id=user.id
        ).first()
        
        if cashback_payout:
            conv_dict['cashback_payout'] = cashback_payout.to_dict()
        
        return jsonify(conv_dict)
    except ValueError:
        return jsonify({'error': 'Invalid user ID or transaction ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


