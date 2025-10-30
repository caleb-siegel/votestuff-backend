"""
List routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product
from sqlalchemy import desc
import uuid

@api_bp.route('/lists', methods=['GET'])
def get_lists():
    """Get lists with filters"""
    from sqlalchemy.orm import joinedload
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', 'approved')
    category_id = request.args.get('category_id', type=str)
    sort_by = request.args.get('sort_by', 'newest')  # newest, votes, views
    
    query = List.query.options(
        joinedload(List.category),
        joinedload(List.creator)
    )
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    # Filter by category
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Sort
    if sort_by == 'votes':
        query = query.order_by(desc(List.total_votes))
    elif sort_by == 'views':
        query = query.order_by(desc(List.view_count))
    else:
        query = query.order_by(desc(List.created_at))
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Build response with category and creator data
    lists_data = []
    for lst in pagination.items:
        list_dict = lst.to_dict()
        if lst.category:
            list_dict['category'] = lst.category.to_dict()
        if lst.creator:
            list_dict['creator'] = lst.creator.to_dict()
        lists_data.append(list_dict)
    
    return jsonify({
        'lists': lists_data,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages
    })

@api_bp.route('/lists/<list_id>', methods=['GET'])
def get_list(list_id):
    """Get single list with products"""
    try:
        from sqlalchemy.orm import joinedload
        from models.product_link import ProductLink
        from models.retailer import Retailer
        
        lst = List.query.options(
            joinedload(List.products).joinedload(Product.product_links).joinedload(ProductLink.retailer)
        ).get_or_404(uuid.UUID(list_id))
        
        # Increment view count (analytics tracking)
        lst.view_count += 1
        db.session.commit()
        
        list_data = lst.to_dict()
        # Products are returned in the order defined by their relationship
        # The Product model relationship includes: order_by='Product.rank'
        # This means products are automatically sorted by their rank field (1, 2, 3, etc.)
        # which was calculated by update_list_ranking() based on votes.
        # Rank 1 = highest (best net score + upvote %), Rank 2 = second, etc.
        list_data['products'] = [product.to_dict() for product in lst.products]
        list_data['creator'] = lst.creator.to_dict()
        if lst.category:
            list_data['category'] = lst.category.to_dict()
        
        return jsonify(list_data)
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400

@api_bp.route('/lists', methods=['POST'])
def create_list():
    """Create a new list"""
    data = request.get_json()
    
    # TODO: Add authentication check
    if not data or not data.get('title'):
        return jsonify({'error': 'Title required'}), 400
    
    creator_id = data.get('creator_id')
    if not creator_id:
        return jsonify({'error': 'Creator ID required'}), 400
    
    try:
        new_list = List(
            id=uuid.uuid4(),
            title=data.get('title'),
            description=data.get('description'),
            slug=data.get('slug') or data.get('title').lower().replace(' ', '-'),
            creator_id=creator_id,
            category_id=data.get('category_id'),
            status='pending'
        )
        db.session.add(new_list)
        db.session.commit()
        
        return jsonify({
            'message': 'List created successfully',
            'list': new_list.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/lists/trending', methods=['GET'])
def get_trending_lists():
    """Get trending lists based on recent votes"""
    from sqlalchemy.orm import joinedload
    
    query = List.query.options(
        joinedload(List.category),
        joinedload(List.creator)
    ).filter_by(status='approved')
    query = query.order_by(desc(List.total_votes))
    
    # Get top 10
    trending = query.limit(10).all()
    
    # Build response with category and creator data
    lists_data = []
    for lst in trending:
        list_dict = lst.to_dict()
        if lst.category:
            list_dict['category'] = lst.category.to_dict()
        if lst.creator:
            list_dict['creator'] = lst.creator.to_dict()
        lists_data.append(list_dict)
    
    return jsonify({
        'lists': lists_data
    })

