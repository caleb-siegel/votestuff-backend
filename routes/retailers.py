"""
Retailer routes
"""

from flask import request, jsonify
from . import api_bp
from models import db
from models.retailer import Retailer
import uuid
import re

@api_bp.route('/retailers', methods=['GET'])
def get_retailers():
    """Get all retailers or search by name"""
    search = request.args.get('search', '').strip()
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    
    query = Retailer.query.filter_by(is_active=is_active) if is_active else Retailer.query
    
    if search:
        query = query.filter(Retailer.name.ilike(f'%{search}%'))
    
    retailers = query.order_by(Retailer.name).limit(50).all()
    
    return jsonify({
        'retailers': [r.to_dict() for r in retailers]
    }), 200

@api_bp.route('/retailers/<retailer_id>', methods=['GET'])
def get_retailer(retailer_id):
    """Get a single retailer by ID"""
    try:
        retailer_uuid = uuid.UUID(retailer_id)
    except ValueError:
        return jsonify({'error': 'Invalid retailer ID'}), 400
    
    retailer = Retailer.query.get(retailer_uuid)
    if not retailer:
        return jsonify({'error': 'Retailer not found'}), 404
    
    return jsonify({
        'retailer': retailer.to_dict()
    }), 200

@api_bp.route('/retailers', methods=['POST'])
def create_retailer():
    """Create a new retailer"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Retailer name is required'}), 400
    
    name = data.get('name').strip()
    if not name:
        return jsonify({'error': 'Retailer name cannot be empty'}), 400
    
    # Check if retailer with same name already exists
    existing = Retailer.query.filter_by(name=name).first()
    if existing:
        return jsonify({
            'error': 'Retailer with this name already exists',
            'retailer': existing.to_dict()
        }), 409
    
    # Generate slug from name
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    
    # Ensure slug is unique
    base_slug = slug
    counter = 1
    while Retailer.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    retailer = Retailer(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        description=data.get('description'),
        affiliate_network=data.get('affiliate_network'),
        commission_rate=data.get('commission_rate'),
        base_affiliate_link=data.get('base_affiliate_link'),
        logo_url=data.get('logo_url'),
        website_url=data.get('website_url'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(retailer)
    db.session.commit()
    
    return jsonify({
        'message': 'Retailer created successfully',
        'retailer': retailer.to_dict()
    }), 201

