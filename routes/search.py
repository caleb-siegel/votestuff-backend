"""
Search routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product, Category
from sqlalchemy import or_, and_
import re

@api_bp.route('/search', methods=['GET'])
def search():
    """Search across lists, products, and categories.
    
    The goal is to surface the right lists for users based on what they search for.
    - If searching for a product, show lists that contain that product
    - If searching for a category, show lists in that category
    - Also show direct matches on list titles/descriptions
    
    The search uses flexible word matching:
    - Exact phrase match (e.g., "mens coat" matches "mens coat...")
    - Word-by-word match (e.g., "mens coat" matches "best men's coats")
    - All query words must appear somewhere in the title/description
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    # Normalize query to lowercase
    query_lower = query.lower()
    
    # Split into words (split on spaces and hyphens)
    # This handles "mens coat" -> ["mens", "coat"]
    query_words = [w.strip() for w in re.split(r'[\s\-]+', query_lower) if w.strip()]
    
    # Normalize words: remove apostrophes for better matching
    # "mens" and "men's" both become "mens" for matching purposes
    normalized_query_words = []
    for word in query_words:
        # Remove apostrophes and the 's' that follows
        normalized = word.replace("'s", "s").replace("'", "")
        normalized_query_words.append(normalized)
    
    # Create patterns: exact phrase AND word-by-word matching
    exact_phrase_pattern = f'%{query_lower}%'
    
    # Build filters: match exact phrase OR (all words appear in title/description)
    # For word-by-word: all words must appear (AND logic)
    title_filters = [List.title.ilike(exact_phrase_pattern)]
    desc_filters = []
    
    if len(normalized_query_words) > 1:
        # Word-by-word matching: all words must appear
        # For each word, check multiple variations to handle apostrophes
        # e.g., "mens" should match "mens", "men's", or "men"
        word_title_conditions = []
        for i, norm_word in enumerate(normalized_query_words):
            orig_word = query_words[i]
            # Build variations to check - handle apostrophes in both query and database
            word_variations = [norm_word, orig_word]  # Always check both normalized and original
            
            # If word ends with "s", also check without it (e.g., "mens" -> "men")
            # This helps match "mens" with "men's" in database
            if norm_word.endswith('s') and len(norm_word) > 1:
                base_word = norm_word[:-1]  # Remove final 's'
                word_variations.append(base_word)
                word_variations.append(f"{base_word}'s")  # Check possessive form
            
            # Remove duplicates while preserving order
            seen = set()
            unique_variations = []
            for var in word_variations:
                if var not in seen:
                    seen.add(var)
                    unique_variations.append(var)
            
            # Create OR filter for this word's variations
            word_or_filters = [List.title.ilike(f'%{var}%') for var in unique_variations]
            if word_or_filters:
                word_title_conditions.append(or_(*word_or_filters))
        
        # All words must appear (AND logic)
        if word_title_conditions:
            title_filters.append(and_(*word_title_conditions))
        
        # Same for description
        word_desc_conditions = []
        for i, norm_word in enumerate(normalized_query_words):
            orig_word = query_words[i]
            word_variations = [norm_word, orig_word]
            
            # If word ends with "s", also check without it
            if norm_word.endswith('s') and len(norm_word) > 1:
                base_word = norm_word[:-1]
                word_variations.append(base_word)
                word_variations.append(f"{base_word}'s")
            
            # Remove duplicates
            seen = set()
            unique_variations = []
            for var in word_variations:
                if var not in seen:
                    seen.add(var)
                    unique_variations.append(var)
            
            word_or_filters = [List.description.ilike(f'%{var}%') for var in unique_variations]
            if word_or_filters:
                word_desc_conditions.append(or_(*word_or_filters))
        
        if word_desc_conditions:
            desc_filters.append(and_(*word_desc_conditions))
    
    # Also handle single word case
    if len(normalized_query_words) == 1:
        word_pattern = f'%{normalized_query_words[0]}%'
        title_filters.append(List.title.ilike(word_pattern))
        desc_filters.append(List.description.ilike(word_pattern))
    
    # Add exact phrase match for description
    desc_filters.append(List.description.ilike(exact_phrase_pattern))
    
    # Search lists by title/description
    lists_by_title = List.query.filter(
        or_(
            *title_filters,
            *desc_filters
        )
    ).filter_by(status='approved').all()
    
    # Search products - same flexible matching
    exact_phrase_pattern = f'%{query_lower}%'
    product_name_filters = [Product.name.ilike(exact_phrase_pattern)]
    product_desc_filters = [Product.description.ilike(exact_phrase_pattern)]
    
    if len(normalized_query_words) > 1:
        word_name_filters = [Product.name.ilike(f'%{word}%') for word in normalized_query_words]
        if word_name_filters:
            product_name_filters.append(and_(*word_name_filters))
        
        word_desc_filters = [Product.description.ilike(f'%{word}%') for word in normalized_query_words]
        if word_desc_filters:
            product_desc_filters.append(and_(*word_desc_filters))
    elif len(normalized_query_words) == 1:
        word_pattern = f'%{normalized_query_words[0]}%'
        product_name_filters.append(Product.name.ilike(word_pattern))
        product_desc_filters.append(Product.description.ilike(word_pattern))
    
    products = Product.query.filter(
        or_(
            *product_name_filters,
            *product_desc_filters
        )
    ).limit(20).all()
    
    # Get lists that contain matching products
    product_list_ids = [prod.list_id for prod in products]
    lists_by_products = List.query.filter(
        List.id.in_(product_list_ids)
    ).filter_by(status='approved').all()
    
    # Search categories - same flexible matching
    exact_phrase_pattern = f'%{query_lower}%'
    category_name_filters = [Category.name.ilike(exact_phrase_pattern)]
    category_desc_filters = [Category.description.ilike(exact_phrase_pattern)]
    
    if len(normalized_query_words) > 1:
        word_name_filters = [Category.name.ilike(f'%{word}%') for word in normalized_query_words]
        if word_name_filters:
            category_name_filters.append(and_(*word_name_filters))
        
        word_desc_filters = [Category.description.ilike(f'%{word}%') for word in normalized_query_words]
        if word_desc_filters:
            category_desc_filters.append(and_(*word_desc_filters))
    elif len(normalized_query_words) == 1:
        word_pattern = f'%{normalized_query_words[0]}%'
        category_name_filters.append(Category.name.ilike(word_pattern))
        category_desc_filters.append(Category.description.ilike(word_pattern))
    
    categories = Category.query.filter(
        or_(
            *category_name_filters,
            *category_desc_filters
        )
    ).limit(10).all()
    
    # Get lists in matching categories
    category_ids = [cat.id for cat in categories]
    lists_by_category = List.query.filter(
        List.category_id.in_(category_ids)
    ).filter_by(status='approved').all()
    
    # Combine all lists, removing duplicates
    all_lists = {}
    for lst in lists_by_title + lists_by_products + lists_by_category:
        all_lists[str(lst.id)] = lst
    
    # Limit to top 15 lists (prioritize those matching multiple criteria)
    # Sort by: lists matching title first, then by view_count/total_votes
    sorted_lists = sorted(
        all_lists.values(),
        key=lambda x: (
            str(x.id) not in [str(l.id) for l in lists_by_title],  # Title matches first
            -(x.view_count + x.total_votes)  # Then by popularity
        )
    )[:15]
    
    # For each product, include its list info
    products_with_lists = []
    for prod in products[:10]:  # Limit products displayed
        product_dict = prod.to_dict()
        # Include basic list info
        if prod.list:
            product_dict['list'] = {
                'id': str(prod.list.id),
                'title': prod.list.title,
                'slug': prod.list.slug,
            }
        products_with_lists.append(product_dict)
    
    return jsonify({
        'lists': [lst.to_dict() for lst in sorted_lists],
        'products': products_with_lists,
        'categories': [cat.to_dict() for cat in categories],
        'query': query
    })

