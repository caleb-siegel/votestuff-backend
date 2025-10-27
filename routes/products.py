"""
Product routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Product, List
import uuid

@api_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product"""
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        return jsonify(product.to_dict())
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400

@api_bp.route('/lists/<list_id>/products', methods=['POST'])
def add_product(list_id):
    """Add product to a list"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('affiliate_url'):
        return jsonify({'error': 'Name and affiliate URL required'}), 400
    
    try:
        # Verify list exists
        lst = List.query.get_or_404(uuid.UUID(list_id))
        
        new_product = Product(
            id=uuid.uuid4(),
            name=data.get('name'),
            description=data.get('description'),
            image_url=data.get('image_url'),
            affiliate_url=data.get('affiliate_url'),
            product_url=data.get('product_url'),
            list_id=list_id
        )
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product added successfully',
            'product': new_product.to_dict()
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<product_id>/click', methods=['POST'])
def track_click(product_id):
    """Track affiliate click"""
    # TODO: Implement click tracking
    # This should increment click_count and create AffiliateClick record
    return jsonify({'message': 'Click tracked'})

