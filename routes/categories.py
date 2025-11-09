"""
Category routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Category, List
from sqlalchemy import func
import uuid

# Cache for category tree to avoid reloading on every request
_category_tree_cache = None
_category_tree_cache_timestamp = None

def _get_category_tree():
    """Get or build cached category tree"""
    global _category_tree_cache, _category_tree_cache_timestamp
    from datetime import datetime, timedelta
    
    # Cache for 5 minutes
    if _category_tree_cache is None or (
        _category_tree_cache_timestamp and 
        datetime.utcnow() - _category_tree_cache_timestamp > timedelta(minutes=5)
    ):
        all_categories = Category.query.all()
        children_map = {}
        for cat in all_categories:
            if cat.parent_id:
                parent_id_str = str(cat.parent_id)
                if parent_id_str not in children_map:
                    children_map[parent_id_str] = []
                children_map[parent_id_str].append(cat)
        _category_tree_cache = children_map
        _category_tree_cache_timestamp = datetime.utcnow()
    
    return _category_tree_cache

def get_all_descendant_ids(category_id):
    """Get all descendant category IDs (including the category itself) recursively"""
    children_map = _get_category_tree()
    
    # Start with the category itself
    descendant_ids = [category_id]
    visited = {str(category_id)}  # Track visited to prevent infinite loops
    
    # Recursively collect all descendant IDs
    def collect_descendants(cat_id):
        cat_id_str = str(cat_id)
        if cat_id_str in children_map:
            for child in children_map[cat_id_str]:
                child_id_str = str(child.id)
                # Only process if not already visited (prevents circular references)
                if child_id_str not in visited:
                    visited.add(child_id_str)
                    descendant_ids.append(child.id)
                    collect_descendants(child.id)
    
    collect_descendants(category_id)
    return descendant_ids

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories, optionally in hierarchical format"""
    hierarchical = request.args.get('hierarchical', 'false').lower() == 'true'
    
    if hierarchical:
        # Optimized: Load all categories in one query
        # Load all categories at once, then build hierarchy in memory
        all_categories = Category.query.all()
        
        # Get list counts for all categories (including subcategories)
        # First, get direct counts
        direct_counts = db.session.query(
            List.category_id,
            func.count(List.id).label('count')
        ).filter(
            List.status == 'approved'
        ).group_by(List.category_id).all()
        
        # Create a dictionary for direct counts
        direct_count_dict = {str(cat_id): count for cat_id, count in direct_counts}
        
        # Build count dict that includes subcategories (optimized - build all at once)
        children_map = _get_category_tree()
        count_dict = {}
        
        # Build descendant map for all categories in one pass
        def build_descendant_map():
            """Build a map of category_id -> all descendant IDs"""
            descendant_map = {}
            
            def get_descendants(cat_id):
                """Get all descendants for a category (with memoization)"""
                cat_id_str = str(cat_id)
                if cat_id_str in descendant_map:
                    return descendant_map[cat_id_str]
                
                descendants = [cat_id]
                visited = {cat_id_str}
                
                def collect(cid):
                    cid_str = str(cid)
                    if cid_str in children_map:
                        for child in children_map[cid_str]:
                            child_id_str = str(child.id)
                            if child_id_str not in visited:
                                visited.add(child_id_str)
                                descendants.append(child.id)
                                collect(child.id)
                
                collect(cat_id)
                descendant_map[cat_id_str] = descendants
                return descendants
            
            return get_descendants
        
        get_descendants = build_descendant_map()
        
        # Calculate counts for all categories
        for cat in all_categories:
            cat_id_str = str(cat.id)
            descendant_ids = get_descendants(cat.id)
            total_count = sum(direct_count_dict.get(str(desc_id), 0) for desc_id in descendant_ids)
            count_dict[cat_id_str] = total_count
        
        # Build hierarchy in memory (much faster than recursive queries)
        # First, organize categories by parent_id
        categories_by_parent = {}
        top_level = []
        
        for cat in all_categories:
            parent_id_str = str(cat.parent_id) if cat.parent_id else None
            if parent_id_str:
                if parent_id_str not in categories_by_parent:
                    categories_by_parent[parent_id_str] = []
                categories_by_parent[parent_id_str].append(cat)
            else:
                top_level.append(cat)
        
        def build_category_dict(cat, count_dict, categories_by_parent):
            """Build category dict with list count recursively"""
            cat_id_str = str(cat.id)
            result = {
                'id': cat_id_str,
                'name': cat.name,
                'slug': cat.slug,
                'description': cat.description,
                'icon': cat.icon,
                'parent_id': str(cat.parent_id) if cat.parent_id else None,
                'list_count': count_dict.get(cat_id_str, 0)
            }
            # Get children from the organized dict
            children = categories_by_parent.get(cat_id_str, [])
            if children:
                result['children'] = [
                    build_category_dict(child, count_dict, categories_by_parent) 
                    for child in children
                ]
            return result
        
        return jsonify({
            'categories': [build_category_dict(cat, count_dict, categories_by_parent) for cat in top_level]
        })
    else:
        # Return flat list with optimized list counts
        categories = Category.query.all()
        
        # Get list counts for all categories (including subcategories)
        # First, get direct counts
        direct_counts = db.session.query(
            List.category_id,
            func.count(List.id).label('count')
        ).filter(
            List.status == 'approved'
        ).group_by(List.category_id).all()
        
        # Create a dictionary for direct counts
        direct_count_dict = {str(cat_id): count for cat_id, count in direct_counts}
        
        # Build count dict that includes subcategories (optimized - build all at once)
        children_map = _get_category_tree()
        count_dict = {}
        
        # Build descendant map for all categories in one pass
        def build_descendant_map():
            """Build a map of category_id -> all descendant IDs"""
            descendant_map = {}
            
            def get_descendants(cat_id):
                """Get all descendants for a category (with memoization)"""
                cat_id_str = str(cat_id)
                if cat_id_str in descendant_map:
                    return descendant_map[cat_id_str]
                
                descendants = [cat_id]
                visited = {cat_id_str}
                
                def collect(cid):
                    cid_str = str(cid)
                    if cid_str in children_map:
                        for child in children_map[cid_str]:
                            child_id_str = str(child.id)
                            if child_id_str not in visited:
                                visited.add(child_id_str)
                                descendants.append(child.id)
                                collect(child.id)
                
                collect(cat_id)
                descendant_map[cat_id_str] = descendants
                return descendants
            
            return get_descendants
        
        get_descendants = build_descendant_map()
        
        # Calculate counts for all categories
        for cat in categories:
            cat_id_str = str(cat.id)
            descendant_ids = get_descendants(cat.id)
            total_count = sum(direct_count_dict.get(str(desc_id), 0) for desc_id in descendant_ids)
            count_dict[cat_id_str] = total_count
        
        return jsonify({
            'categories': [cat.to_dict(count_dict=count_dict) for cat in categories]
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

