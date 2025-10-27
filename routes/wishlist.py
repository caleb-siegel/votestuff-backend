"""
Wishlist routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Wishlist, Product
from sqlalchemy.exc import IntegrityError
import uuid

@api_bp.route('/users/<user_id>/wishlist', methods=['GET'])
def get_wishlist(user_id):
    """Get user's wishlist"""
    try:
        user_id_uuid = uuid.UUID(user_id)
        wishlist_items = Wishlist.query.filter_by(user_id=user_id_uuid).all()
        
        products = [Product.query.get(item.product_id).to_dict() for item in wishlist_items]
        
        return jsonify({
            'items': products,
            'count': len(products)
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400

@api_bp.route('/users/<user_id>/wishlist', methods=['POST'])
def add_to_wishlist(user_id):
    """Add product to wishlist"""
    data = request.get_json()
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    try:
        new_item = Wishlist(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            product_id=uuid.UUID(product_id)
        )
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({
            'message': 'Added to wishlist',
            'item': new_item.to_dict()
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Product already in wishlist'}), 409
    except ValueError:
        return jsonify({'error': 'Invalid IDs'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>/wishlist/<product_id>', methods=['DELETE'])
def remove_from_wishlist(user_id, product_id):
    """Remove product from wishlist"""
    try:
        item = Wishlist.query.filter_by(
            user_id=uuid.UUID(user_id),
            product_id=uuid.UUID(product_id)
        ).first()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'message': 'Removed from wishlist'}), 200
    except ValueError:
        return jsonify({'error': 'Invalid IDs'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

