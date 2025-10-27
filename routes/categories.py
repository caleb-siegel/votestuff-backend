"""
Category routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Category
import uuid

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    return jsonify({
        'categories': [cat.to_dict() for cat in categories]
    })

@api_bp.route('/categories/<category_id>', methods=['GET'])
def get_category(category_id):
    """Get single category"""
    try:
        category = Category.query.get_or_404(uuid.UUID(category_id))
        return jsonify(category.to_dict())
    except ValueError:
        return jsonify({'error': 'Invalid category ID'}), 400

@api_bp.route('/categories/slug/<slug>', methods=['GET'])
def get_category_by_slug(slug):
    """Get category by slug"""
    category = Category.query.filter_by(slug=slug).first()
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    return jsonify(category.to_dict())

