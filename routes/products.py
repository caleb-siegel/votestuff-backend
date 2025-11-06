"""
Product routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Product, List, ProductLink, AffiliateClick
from datetime import datetime
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
    """Track affiliate click and return tracking URL"""
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        data = request.get_json() or {}
        
        # Get product_link_id if provided (for ProductLink tracking)
        product_link_id = data.get('product_link_id')
        if product_link_id:
            try:
                product_link = ProductLink.query.get(uuid.UUID(product_link_id))
                if product_link and product_link.product_id != product.id:
                    return jsonify({'error': 'Product link does not match product'}), 400
                url_to_track = product_link.url if product_link else product.affiliate_url
            except ValueError:
                return jsonify({'error': 'Invalid product_link_id'}), 400
        else:
            product_link = None
            url_to_track = product.affiliate_url
        
        # Get user info (optional - can be guest)
        user_id = data.get('user_id')
        if user_id:
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return jsonify({'error': 'Invalid user_id'}), 400
        
        # Get session_id (for anonymous users)
        session_id = data.get('session_id')
        
        # Get tracking info from request headers
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        referrer = request.headers.get('Referer', '')
        
        # Create affiliate click record
        click = AffiliateClick(
            id=uuid.uuid4(),
            list_id=product.list_id,
            product_id=product.id,
            product_link_id=product_link.id if product_link else None,
            user_id=user_id,
            url=url_to_track,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            created_at=datetime.utcnow()
        )
        
        db.session.add(click)
        
        # Increment click count on product link if exists
        if product_link:
            product_link.click_count = (product_link.click_count or 0) + 1
        
        # Increment click count on product
        product.click_count = (product.click_count or 0) + 1
        
        db.session.commit()
        
        # Return click ID and URL for frontend to redirect
        return jsonify({
            'click_id': str(click.id),
            'url': url_to_track,
            'message': 'Click tracked'
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

