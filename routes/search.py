"""
Search routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product, Category
from sqlalchemy import or_

@api_bp.route('/search', methods=['GET'])
def search():
    """Search across lists, products, and categories"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    # Search lists
    lists = List.query.filter(
        or_(
            List.title.ilike(f'%{query}%'),
            List.description.ilike(f'%{query}%')
        )
    ).filter_by(status='approved').limit(10).all()
    
    # Search products
    products = Product.query.filter(
        or_(
            Product.name.ilike(f'%{query}%'),
            Product.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Search categories
    categories = Category.query.filter(
        or_(
            Category.name.ilike(f'%{query}%'),
            Category.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return jsonify({
        'lists': [lst.to_dict() for lst in lists],
        'products': [prod.to_dict() for prod in products],
        'categories': [cat.to_dict() for cat in categories],
        'query': query
    })

