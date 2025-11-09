"""
List routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product, Category
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload
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
    
    # Recursively collect all descendant IDs
    def collect_descendants(cat_id):
        cat_id_str = str(cat_id)
        if cat_id_str in children_map:
            for child in children_map[cat_id_str]:
                descendant_ids.append(child.id)
                collect_descendants(child.id)
    
    collect_descendants(category_id)
    return descendant_ids

@api_bp.route('/lists', methods=['GET'])
def get_lists():
    """Get lists with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', 'approved')
    category_id = request.args.get('category_id', type=str)
    include_subcategories = request.args.get('include_subcategories', 'true').lower() == 'true'
    creator_id = request.args.get('creator_id', type=str)
    sort_by = request.args.get('sort_by', 'newest')  # newest, votes, views
    
    query = List.query.options(
        joinedload(List.category),
        joinedload(List.creator)
    )
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    # Filter by category (including subcategories if requested)
    if category_id:
        try:
            category_uuid = uuid.UUID(category_id)
            if include_subcategories:
                # Get all descendant category IDs (including the category itself)
                descendant_ids = get_all_descendant_ids(category_uuid)
                # Filter by any of these category IDs
                query = query.filter(List.category_id.in_(descendant_ids))
            else:
                # Only filter by the exact category
                query = query.filter_by(category_id=category_uuid)
        except ValueError:
            pass  # Invalid UUID, skip filter
    
    # Filter by creator
    if creator_id:
        try:
            query = query.filter_by(creator_id=uuid.UUID(creator_id))
        except ValueError:
            pass  # Invalid UUID, skip filter
    
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
            joinedload(List.products).joinedload(Product.retailer),
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
    """
    Create a new list with products and product links
    
    Supports both authenticated users and guest submissions.
    For guests, a guest user will be created automatically.
    Status can be 'draft' or 'pending' (defaults to 'pending').
    """
    from models.user import User
    from models.product_link import ProductLink
    from models.retailer import Retailer
    import re
    
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Title required'}), 400
    
    creator_id = data.get('creator_id')
    is_guest = data.get('is_guest', False)
    
    # Determine status
    status = data.get('status', 'pending')  # 'draft' or 'pending'
    if status not in ['draft', 'pending']:
        status = 'pending'
    
    # Validate minimum products requirement (only for pending submissions, not drafts)
    products_data = data.get('products', [])
    if status == 'pending' and (not products_data or len(products_data) < 5):
        return jsonify({'error': 'At least 5 products are required for submission'}), 400
    
    try:
        # Handle guest user creation if needed
        if is_guest or not creator_id:
            # Create or find guest user
            guest_email = f"guest_{uuid.uuid4().hex[:8]}@votestuff.guest"
            guest_user = User.query.filter_by(email=guest_email).first()
            if not guest_user:
                guest_user = User(
                    id=uuid.uuid4(),
                    email=guest_email,
                    display_name='Guest User',
                    password_hash=None,
                    is_active=False,  # Guest users are inactive
                )
                db.session.add(guest_user)
                db.session.flush()  # Get the ID without committing
            creator_id = str(guest_user.id)
        else:
            # Verify authenticated user exists
            creator_id = uuid.UUID(creator_id)
            user = User.query.get(creator_id)
            if not user:
                return jsonify({'error': 'Invalid creator ID'}), 400
        
        # Generate unique slug
        base_slug = data.get('slug') or re.sub(r'[^a-z0-9]+', '-', data.get('title').lower()).strip('-')
        slug = base_slug
        counter = 1
        while List.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
        counter += 1
        
        # Create the list
        new_list = List(
            id=uuid.uuid4(),
            title=data.get('title'),
            description=data.get('description'),
            slug=slug,
            creator_id=creator_id,
            category_id=uuid.UUID(data.get('category_id')) if data.get('category_id') else None,
            status=status
        )
        db.session.add(new_list)
        db.session.flush()  # Get the ID without committing
        
        # Create products with their links
        created_products = []
        for idx, product_data in enumerate(products_data):
            if not product_data.get('name') or not product_data.get('affiliate_url'):
                continue  # Skip invalid products
            
            product = Product(
                id=uuid.uuid4(),
                name=product_data.get('name'),
                description=product_data.get('description'),
                image_url=product_data.get('image_url'),
                affiliate_url=product_data.get('affiliate_url'),
                product_url=product_data.get('product_url'),
                list_id=new_list.id,
                rank=idx + 1  # Initial rank based on order
            )
            db.session.add(product)
            db.session.flush()  # Get the ID
            
            # Create product links if provided
            links_data = product_data.get('links', [])
            # Always create at least one link (the primary affiliate_url)
            if not links_data:
                links_data = [{
                    'url': product_data.get('affiliate_url'),
                    'retailer_name': 'Amazon',  # Default to Amazon if not specified
                    'is_primary': True,
                    'price': product_data.get('price')
                }]
            
            primary_retailer = None
            for link_idx, link_data in enumerate(links_data):
                if not link_data.get('url'):
                    continue
                
                # Find or create retailer
                retailer = None
                retailer_id = link_data.get('retailer_id')
                if retailer_id:
                    # Try to find retailer by ID
                    try:
                        retailer_uuid = uuid.UUID(retailer_id)
                        retailer = Retailer.query.get(retailer_uuid)
                    except ValueError:
                        pass
                
                # If not found by ID, try by name
                if not retailer:
                    retailer_name = link_data.get('retailer_name', 'Amazon')
                    retailer = Retailer.query.filter_by(name=retailer_name).first()
                    if not retailer:
                        # Create retailer if doesn't exist
                        retailer_slug = re.sub(r'[^a-z0-9]+', '-', retailer_name.lower()).strip('-')
                        # Ensure slug is unique
                        base_slug = retailer_slug
                        counter = 1
                        while Retailer.query.filter_by(slug=retailer_slug).first():
                            retailer_slug = f"{base_slug}-{counter}"
                            counter += 1
                        retailer = Retailer(
                            id=uuid.uuid4(),
                            name=retailer_name,
                            slug=retailer_slug,
                            description=f"Retailer: {retailer_name}",
                            is_active=True
                        )
                        db.session.add(retailer)
                        db.session.flush()
                
                # Set primary retailer from first link
                if link_idx == 0 and not primary_retailer:
                    primary_retailer = retailer
                
                product_link = ProductLink(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    retailer_id=retailer.id,
                    url=link_data.get('url'),
                    link_name=link_data.get('link_name'),
                    price=link_data.get('price'),
                    is_affiliate_link=link_data.get('is_affiliate_link', True),
                    is_primary=link_data.get('is_primary', link_idx == 0)
                )
                db.session.add(product_link)
            
            # Set retailer_id on product from first link's retailer
            if primary_retailer:
                product.retailer_id = primary_retailer.id
            
            created_products.append(product)
        
        # Commit everything
        db.session.commit()
        
        # Return the created list with products
        list_dict = new_list.to_dict()
        list_dict['products'] = [p.to_dict() for p in created_products]
        
        return jsonify({
            'message': f'List created successfully as {status}',
            'list': list_dict
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid UUID: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/lists/<list_id>', methods=['PATCH'])
def update_list(list_id):
    """
    Update an existing list (e.g., convert draft to pending, update products)
    
    Only the creator of the list can update it.
    """
    from models.user import User
    from models.product_link import ProductLink
    from models.retailer import Retailer
    import re
    
    try:
        lst = List.query.get_or_404(uuid.UUID(list_id))
        data = request.get_json()
        
        # TODO: Add authentication check to ensure user is the creator
        
        # Update basic list fields
        if data.get('title'):
            lst.title = data.get('title')
            # Regenerate slug if title changed
            base_slug = re.sub(r'[^a-z0-9]+', '-', data.get('title').lower()).strip('-')
            slug = base_slug
            counter = 1
            while List.query.filter(List.id != lst.id, List.slug == slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            lst.slug = slug
        
        if data.get('description') is not None:
            lst.description = data.get('description')
        
        if data.get('category_id') is not None:
            lst.category_id = uuid.UUID(data.get('category_id')) if data.get('category_id') else None
        
        if data.get('status') and data.get('status') in ['draft', 'pending']:
            lst.status = data.get('status')
        
        # If products are provided, update them
        if data.get('products') is not None:
            products_data = data.get('products')
            
            # Validate minimum products for pending status
            if lst.status == 'pending' and (not products_data or len(products_data) < 5):
                return jsonify({'error': 'At least 5 products are required for submission'}), 400
            
            # Delete existing products (cascade will handle product_links)
            for product in lst.products:
                db.session.delete(product)
            
            # Create new products
            created_products = []
            for idx, product_data in enumerate(products_data):
                if not product_data.get('name'):
                    continue
                
                # Get affiliate_url from provided value or first link
                affiliate_url = product_data.get('affiliate_url') or ""
                if not affiliate_url:
                    links_data = product_data.get('links', [])
                    if links_data and len(links_data) > 0 and links_data[0].get('url'):
                        affiliate_url = links_data[0].get('url')
                
                product = Product(
                    id=uuid.uuid4(),
                    name=product_data.get('name'),
                    description=product_data.get('description'),
                    image_url=product_data.get('image_url'),
                    affiliate_url=affiliate_url,
                    product_url=product_data.get('product_url'),
                    list_id=lst.id,
                    rank=idx + 1
                )
                db.session.add(product)
                db.session.flush()
                
                # Create product links
                links_data = product_data.get('links', [])
                if not links_data:
                    # Use affiliate_url as default link
                    links_data = [{
                        'url': product_data.get('affiliate_url') or "",
                        'retailer_name': 'Amazon',
                        'is_primary': True,
                        'price': None
                    }]
                
                primary_retailer = None
                for link_idx, link_data in enumerate(links_data):
                    if not link_data.get('url'):
                        continue
                    
                    # Find or create retailer
                    retailer = None
                    retailer_id = link_data.get('retailer_id')
                    if retailer_id:
                        # Try to find retailer by ID
                        try:
                            retailer_uuid = uuid.UUID(retailer_id)
                            retailer = Retailer.query.get(retailer_uuid)
                        except ValueError:
                            pass
                    
                    # If not found by ID, try by name
                    if not retailer:
                        retailer_name = link_data.get('retailer_name', 'Amazon')
                        retailer = Retailer.query.filter_by(name=retailer_name).first()
                        if not retailer:
                            retailer_slug = re.sub(r'[^a-z0-9]+', '-', retailer_name.lower()).strip('-')
                            # Ensure slug is unique
                            base_slug = retailer_slug
                            counter = 1
                            while Retailer.query.filter_by(slug=retailer_slug).first():
                                retailer_slug = f"{base_slug}-{counter}"
                                counter += 1
                            retailer = Retailer(
                                id=uuid.uuid4(),
                                name=retailer_name,
                                slug=retailer_slug,
                                description=f"Retailer: {retailer_name}",
                                is_active=True
                            )
                            db.session.add(retailer)
                            db.session.flush()
                    
                    # Set primary retailer from first link
                    if link_idx == 0 and not primary_retailer:
                        primary_retailer = retailer
                    
                    product_link = ProductLink(
                        id=uuid.uuid4(),
                        product_id=product.id,
                        retailer_id=retailer.id,
                        url=link_data.get('url'),
                        link_name=link_data.get('link_name'),
                        price=link_data.get('price'),
                        is_affiliate_link=link_data.get('is_affiliate_link', True),
                        is_primary=link_data.get('is_primary', link_idx == 0)
                    )
                    db.session.add(product_link)
                
                # Set retailer_id on product from first link's retailer
                if primary_retailer:
                    product.retailer_id = primary_retailer.id
                
                created_products.append(product)
        
        db.session.commit()
        
        # Return updated list
        list_dict = lst.to_dict()
        if data.get('products') is not None:
            list_dict['products'] = [p.to_dict() for p in lst.products]
        
        return jsonify({
            'message': 'List updated successfully',
            'list': list_dict
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid UUID: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/lists/trending', methods=['GET'])
def get_trending_lists():
    """Get trending lists based on recent votes"""
    from sqlalchemy.orm import joinedload
    
    query = List.query.options(
        joinedload(List.category),
        joinedload(List.creator),
        joinedload(List.products)
    ).filter_by(status='approved')
    query = query.order_by(desc(List.total_votes))
    
    # Get top 10
    trending = query.limit(10).all()
    
    # Build response with category, creator, and top product data
    lists_data = []
    for lst in trending:
        list_dict = lst.to_dict()
        if lst.category:
            list_dict['category'] = lst.category.to_dict()
        if lst.creator:
            list_dict['creator'] = lst.creator.to_dict()
        
        # Find the highest ranked product (rank=1) for this list
        top_product = None
        if lst.products:
            # Products are already ordered by rank due to the relationship definition
            # Rank 1 is the highest/best ranked product
            top_product = next((p for p in lst.products if p.rank == 1), None)
            if not top_product and len(lst.products) > 0:
                # Fallback: if no product has rank=1, use the first product (shouldn't happen but safety check)
                top_product = lst.products[0]
        
        if top_product:
            list_dict['top_product'] = top_product.to_dict()
        
        lists_data.append(list_dict)
    
    return jsonify({
        'lists': lists_data
    })

