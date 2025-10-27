"""
Voting routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Vote, Product, List
import uuid

@api_bp.route('/products/<product_id>/vote', methods=['POST'])
def vote_product(product_id):
    """Vote on a product (up or down)"""
    data = request.get_json()
    vote_type = data.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        user_id = data.get('user_id')
        
        # Check if user already voted
        existing_vote = None
        if user_id:
            existing_vote = Vote.query.filter_by(
                product_id=product.id,
                user_id=user_id
            ).first()
        
        if existing_vote:
            # Update existing vote
            old_type = existing_vote.vote_type
            
            if old_type != vote_type:
                # Update votes count
                if old_type == 'up':
                    product.upvotes -= 1
                else:
                    product.downvotes -= 1
                
                if vote_type == 'up':
                    product.upvotes += 1
                else:
                    product.downvotes += 1
                
                existing_vote.vote_type = vote_type
            else:
                # Cancel vote (toggle off)
                if vote_type == 'up':
                    product.upvotes -= 1
                else:
                    product.downvotes -= 1
                
                db.session.delete(existing_vote)
        else:
            # Create new vote
            new_vote = Vote(
                id=uuid.uuid4(),
                product_id=product.id,
                list_id=product.list_id,
                user_id=user_id if user_id else None,
                vote_type=vote_type,
                session_id=data.get('session_id'),
                ip_address=request.remote_addr
            )
            db.session.add(new_vote)
            
            # Update product vote counts
            if vote_type == 'up':
                product.upvotes += 1
            else:
                product.downvotes += 1
        
        db.session.commit()
        
        # Recalculate ranking for the list
        update_list_ranking(product.list_id)
        
        return jsonify({
            'message': 'Vote recorded',
            'product': product.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<product_id>/vote-status', methods=['GET'])
def get_vote_status(product_id):
    """Get vote status for a user"""
    user_id = request.args.get('user_id')
    
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        
        # Find user's vote
        vote_type = None
        if user_id:
            vote = Vote.query.filter_by(
                product_id=product.id,
                user_id=user_id
            ).first()
            if vote:
                vote_type = vote.vote_type
        
        return jsonify({
            'product_id': str(product.id),
            'user_vote': vote_type,
            'upvotes': product.upvotes,
            'downvotes': product.downvotes,
            'net_score': product.net_score
        })
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400

def update_list_ranking(list_id):
    """Update product rankings within a list"""
    try:
        products = Product.query.filter_by(list_id=list_id).all()
        
        # Sort by net score (desc), then by upvote percentage
        sorted_products = sorted(products, key=lambda p: (-p.net_score, -p.upvote_percentage))
        
        # Update ranks
        for rank, product in enumerate(sorted_products, start=1):
            product.rank = rank
        
        # Update total votes for list
        lst = List.query.get(list_id)
        if lst:
            lst.total_votes = sum(p.upvotes + p.downvotes for p in products)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating ranking: {e}")

