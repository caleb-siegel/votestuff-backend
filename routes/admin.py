"""
Admin routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product, ProductLink, User, ContactSubmission, Payout, Category, Retailer, AffiliateClick, Conversion, Vote
from utils.auth_decorators import require_admin
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_, nullslast
import uuid

@api_bp.route('/admin/lists/pending', methods=['GET'])
@require_admin
def get_pending_lists(current_user):
    """Get all pending lists with full details"""
    try:
        pending_lists = List.query.filter_by(status='pending').order_by(desc(List.created_at)).all()
        
        lists_data = []
        for lst in pending_lists:
            list_dict = lst.to_dict()
            if lst.creator:
                # Include creator info
                list_dict['creator'] = {
                    'id': str(lst.creator.id),
                    'display_name': lst.creator.display_name,
                    'email': lst.creator.email
            }
            # Include full product details
            list_dict['products'] = [product.to_dict() for product in lst.products]
            lists_data.append(list_dict)
        
        return jsonify({
            'lists': lists_data,
            'count': len(lists_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/lists/<list_id>', methods=['PATCH'])
@require_admin
def admin_update_list(current_user, list_id):
    """Update a list (title, description, category, status, notes)"""
    try:
        data = request.get_json()
        try:
            list_uuid = uuid.UUID(list_id)
            lst = List.query.get(list_uuid)
        except ValueError:
            lst = List.query.filter_by(slug=list_id).first()
            
        if not lst:
            return jsonify({'error': 'List not found'}), 404
        
        # Update title if provided
        if 'title' in data:
            lst.title = data['title']
        
        # Update description if provided
        if 'description' in data:
            lst.description = data['description']
        
        # Update category if provided
        if 'category_id' in data:
            if data['category_id']:
                category = Category.query.get(uuid.UUID(data['category_id']))
                if not category:
                    return jsonify({'error': 'Category not found'}), 404
                lst.category_id = uuid.UUID(data['category_id'])
            else:
                lst.category_id = None
        
        # Update status if provided
        if 'status' in data:
            lst.status = data['status']
            if data['status'] == 'approved' and not lst.approved_at:
                lst.approved_at = datetime.utcnow()
        
        # Update admin notes if provided
        if 'admin_notes' in data:
            lst.admin_notes = data['admin_notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'List updated successfully',
            'list': lst.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/lists/<list_id>/approve', methods=['POST'])
@require_admin
def approve_list(current_user, list_id):
    """Approve a list"""
    try:
        data = request.get_json() or {}
        try:
            list_uuid = uuid.UUID(list_id)
            lst = List.query.get(list_uuid)
        except ValueError:
            lst = List.query.filter_by(slug=list_id).first()
            
        if not lst:
            return jsonify({'error': 'List not found'}), 404
        
        # Set category if provided
        if 'category_id' in data and data['category_id']:
            category = Category.query.get(uuid.UUID(data['category_id']))
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            lst.category_id = uuid.UUID(data['category_id'])
        
        # Approve the list
        lst.status = 'approved'
        lst.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'List approved',
            'list': lst.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/lists/<list_id>/reject', methods=['POST'])
@require_admin
def reject_list(current_user, list_id):
    """Reject a list"""
    try:
        data = request.get_json()
        try:
            list_uuid = uuid.UUID(list_id)
            lst = List.query.get(list_uuid)
        except ValueError:
            lst = List.query.filter_by(slug=list_id).first()
            
        if not lst:
            return jsonify({'error': 'List not found'}), 404
        lst.status = 'rejected'
        lst.admin_notes = data.get('notes')
        db.session.commit()
        
        return jsonify({
            'message': 'List rejected',
            'list': lst.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid list ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/products/<product_id>', methods=['PATCH'])
@require_admin
def update_product(current_user, product_id):
    """Update a product (name, description, image_url, retailer_id)"""
    try:
        data = request.get_json()
        product = Product.query.get_or_404(uuid.UUID(product_id))
        
        # Update name if provided
        if 'name' in data:
            product.name = data['name']
        
        # Update description if provided
        if 'description' in data:
            product.description = data['description']
        
        # Update image URL if provided
        if 'image_url' in data:
            product.image_url = data['image_url']
        
        # Update retailer if provided
        if 'retailer_id' in data:
            if data['retailer_id']:
                retailer = Retailer.query.get(uuid.UUID(data['retailer_id']))
                if not retailer:
                    return jsonify({'error': 'Retailer not found'}), 404
                product.retailer_id = uuid.UUID(data['retailer_id'])
            else:
                product.retailer_id = None
        
        # Update brand if provided
        if 'brand_id' in data:
            if data['brand_id']:
                brand = Retailer.query.get(uuid.UUID(data['brand_id']))
                if not brand:
                    return jsonify({'error': 'Brand not found'}), 404
                product.brand_id = uuid.UUID(data['brand_id'])
            else:
                product.brand_id = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/product-links', methods=['POST'])
@require_admin
def create_product_link(current_user):
    """Create a new product link"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('product_id') or not data.get('url'):
            return jsonify({'error': 'product_id and url are required'}), 400
        
        # Verify product exists
        product = Product.query.get(uuid.UUID(data['product_id']))
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Verify retailer if provided
        retailer_id = None
        if data.get('retailer_id'):
            retailer = Retailer.query.get(uuid.UUID(data['retailer_id']))
            if not retailer:
                return jsonify({'error': 'Retailer not found'}), 404
            retailer_id = uuid.UUID(data['retailer_id'])
        
        # Create new product link
        new_link = ProductLink(
            id=uuid.uuid4(),
            product_id=uuid.UUID(data['product_id']),
            retailer_id=retailer_id,
            url=data['url'],
            price=data.get('price'),
            link_name=data.get('link_name'),
            is_affiliate_link=data.get('is_affiliate_link', True),
            is_primary=data.get('is_primary', False)
        )
        
        db.session.add(new_link)
        db.session.commit()
        
        return jsonify({
            'message': 'Product link created successfully',
            'product_link': new_link.to_dict()
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid ID format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/product-links/<link_id>', methods=['PATCH'])
@require_admin
def update_product_link(current_user, link_id):
    """Update a product link (url, price, retailer_id)"""
    try:
        data = request.get_json()
        link = ProductLink.query.get_or_404(uuid.UUID(link_id))
        
        # Update URL if provided
        if 'url' in data:
            link.url = data['url']
        
        # Update price if provided
        if 'price' in data:
            link.price = data['price']
        
        # Update link name if provided
        if 'link_name' in data:
            link.link_name = data['link_name']
        
        # Update retailer if provided
        if 'retailer_id' in data:
            if data['retailer_id']:
                retailer = Retailer.query.get(uuid.UUID(data['retailer_id']))
                if not retailer:
                    return jsonify({'error': 'Retailer not found'}), 404
                link.retailer_id = uuid.UUID(data['retailer_id'])
            else:
                link.retailer_id = None
        
        # Update is_primary if provided
        if 'is_primary' in data:
            link.is_primary = data['is_primary']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product link updated successfully',
            'product_link': link.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid link ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/product-links/<link_id>', methods=['DELETE'])
@require_admin
def delete_product_link(current_user, link_id):
    """Delete a product link"""
    try:
        link = ProductLink.query.get_or_404(uuid.UUID(link_id))
        
        db.session.delete(link)
        db.session.commit()
        
        return jsonify({
            'message': 'Product link deleted successfully'
        })
    except ValueError:
        return jsonify({'error': 'Invalid link ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/users', methods=['GET'])
@require_admin
def get_users(current_user):
    """Get all users with admin status"""
    try:
        # Get query parameters for pagination and search
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        
        query = User.query
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search}%'),
                    User.display_name.ilike(f'%{search}%')
                )
            )
        
        # Order by created date descending
        query = query.order_by(desc(User.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users_data = []
        for user in pagination.items:
            users_data.append({
                'id': str(user.id),
                'email': user.email,
                'display_name': user.display_name,
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            'users': users_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/users/<user_id>', methods=['PATCH'])
@require_admin
def update_user_admin_status(current_user, user_id):
    """Update user admin status"""
    try:
        data = request.get_json()
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        # Prevent user from removing their own admin status
        if str(user.id) == str(current_user.id) and 'is_admin' in data and not data['is_admin']:
            return jsonify({'error': 'Cannot remove your own admin status'}), 400
        
        # Update admin status if provided
        if 'is_admin' in data:
            user.is_admin = bool(data['is_admin'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'display_name': user.display_name,
                'is_admin': user.is_admin
            }
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/analytics/dashboard', methods=['GET'])
@require_admin
def get_dashboard_analytics(current_user):
    """Get comprehensive dashboard analytics"""
    try:
        # Date range for trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Total counts
        total_users = User.query.count()
        total_lists = List.query.count()
        pending_lists = List.query.filter_by(status='pending').count()
        approved_lists = List.query.filter_by(status='approved').count()
        rejected_lists = List.query.filter_by(status='rejected').count()
        total_votes = Vote.query.count()
        total_clicks = AffiliateClick.query.count()
        total_conversions = Conversion.query.count()
        
        # Revenue stats
        revenue_data = db.session.query(
            func.sum(Conversion.revenue),
            func.sum(Conversion.commission)
        ).first()
        
        total_revenue = float(revenue_data[0]) if revenue_data[0] else 0
        total_commission = float(revenue_data[1]) if revenue_data[1] else 0
        
        # Recent trends (last 30 days)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_lists = List.query.filter(List.created_at >= thirty_days_ago).count()
        recent_clicks = AffiliateClick.query.filter(AffiliateClick.created_at >= thirty_days_ago).count()
        recent_conversions = Conversion.query.filter(Conversion.converted_at >= thirty_days_ago).count()
        
        # Top performing lists (by clicks)
        top_lists = db.session.query(
            List.id,
            List.title,
            List.slug,
            func.count(AffiliateClick.id).label('click_count')
        ).join(
            AffiliateClick, List.id == AffiliateClick.list_id
        ).group_by(
            List.id, List.title, List.slug
        ).order_by(
            desc('click_count')
        ).limit(10).all()
        
        top_lists_data = [{
            'id': str(lst.id),
            'title': lst.title,
            'slug': lst.slug,
            'clicks': lst.click_count
        } for lst in top_lists]

        # Top performing lists (by votes)
        top_lists_votes = List.query.order_by(desc(List.total_votes)).limit(10).all()
        top_lists_votes_data = [{
            'id': str(lst.id),
            'title': lst.title,
            'slug': lst.slug,
            'votes': lst.total_votes
        } for lst in top_lists_votes]

        # Top performing lists (by views)
        top_lists_views = List.query.order_by(desc(List.view_count)).limit(10).all()
        top_lists_views_data = [{
            'id': str(lst.id),
            'title': lst.title,
            'slug': lst.slug,
            'views': lst.view_count
        } for lst in top_lists_views]
        
        # Recent conversions
        recent_conversions_query = Conversion.query.order_by(desc(Conversion.converted_at)).limit(10).all()
        recent_conversions_data = [conv.to_dict() for conv in recent_conversions_query]
        
        # Daily clicks, conversions, and votes for the last 30 days
        daily_stats = []
        for i in range(30):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_clicks = AffiliateClick.query.filter(
                AffiliateClick.created_at >= day_start,
                AffiliateClick.created_at < day_end
            ).count()
            
            day_conversions = Conversion.query.filter(
                Conversion.converted_at >= day_start,
                Conversion.converted_at < day_end
            ).count()
            
            day_votes = Vote.query.filter(
                Vote.created_at >= day_start,
                Vote.created_at < day_end
            ).count()
            
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'clicks': day_clicks,
                'conversions': day_conversions,
                'votes': day_votes
            })
        
        daily_stats.reverse()  # Oldest to newest
        
        return jsonify({
            'totals': {
                'users': total_users,
                'lists': total_lists,
                'pending_lists': pending_lists,
                'approved_lists': approved_lists,
                'rejected_lists': rejected_lists,
                'votes': total_votes,
                'clicks': total_clicks,
                'conversions': total_conversions,
                'revenue': total_revenue,
                'commission': total_commission
            },
            'recent_trends': {
                'users': recent_users,
                'lists': recent_lists,
                'clicks': recent_clicks,
                'conversions': recent_conversions
            },
            'top_lists': top_lists_data,
            'top_lists_clicks': top_lists_data,
            'top_lists_votes': top_lists_votes_data,
            'top_lists_views': top_lists_views_data,
            'recent_conversions': recent_conversions_data,
            'daily_stats': daily_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/contact-submissions', methods=['GET'])
@require_admin
def get_contact_submissions(current_user):
    """Get all contact submissions (admin)"""
    submissions = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    
    return jsonify({
        'submissions': [sub.to_dict() for sub in submissions]
    })


@api_bp.route('/admin/payouts', methods=['GET'])
@require_admin
def get_payouts(current_user):
    """Get all payouts (admin)"""
    payouts = Payout.query.order_by(Payout.created_at.desc()).all()
    
    return jsonify({
        'payouts': [payout.to_dict() for payout in payouts]
    })


@api_bp.route('/admin/affiliate-clicks', methods=['GET'])
@require_admin
def get_affiliate_clicks(current_user):
    """Get all affiliate clicks with pagination and joined data"""
    try:
        # Get query parameters for pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get sort parameters
        sort_by = request.args.get('sort_by', 'created_at').strip()
        sort_order = request.args.get('sort_order', 'desc').strip().lower()
        
        # Validate sort parameters
        valid_sort_columns = [
            'created_at', 'converted_at', 'has_converted',
            'user_email', 'user_display_name',
            'product_name',
            'list_title',
            'retailer_name',
            'conversion_revenue', 'conversion_commission', 'conversion_status'
        ]
        if sort_by not in valid_sort_columns:
            sort_by = 'created_at'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Get filter parameters
        user_search = request.args.get('user_search', '').strip()
        product_search = request.args.get('product_search', '').strip()
        list_search = request.args.get('list_search', '').strip()
        retailer_id = request.args.get('retailer_id', '').strip()
        has_converted = request.args.get('has_converted', '').strip()
        conversion_status = request.args.get('conversion_status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        url_search = request.args.get('url_search', '').strip()
        
        # Build query with joins
        query = db.session.query(
            AffiliateClick,
            User,
            Product,
            List,
            ProductLink,
            Retailer,
            Conversion
        ).outerjoin(
            User, AffiliateClick.user_id == User.id
        ).join(
            Product, AffiliateClick.product_id == Product.id
        ).join(
            List, AffiliateClick.list_id == List.id
        ).outerjoin(
            ProductLink, AffiliateClick.product_link_id == ProductLink.id
        ).outerjoin(
            Retailer, ProductLink.retailer_id == Retailer.id
        ).outerjoin(
            Conversion, AffiliateClick.id == Conversion.click_id
        )
        
        # Apply filters
        if user_search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{user_search}%'),
                    User.display_name.ilike(f'%{user_search}%')
                )
            )
        
        if product_search:
            query = query.filter(Product.name.ilike(f'%{product_search}%'))
        
        if list_search:
            query = query.filter(
                or_(
                    List.title.ilike(f'%{list_search}%'),
                    List.slug.ilike(f'%{list_search}%')
                )
            )
        
        if retailer_id:
            try:
                retailer_uuid = uuid.UUID(retailer_id)
                query = query.filter(Retailer.id == retailer_uuid)
            except ValueError:
                pass  # Invalid UUID, ignore filter
        
        if has_converted:
            if has_converted.lower() == 'true':
                query = query.filter(AffiliateClick.has_converted == True)
            elif has_converted.lower() == 'false':
                query = query.filter(AffiliateClick.has_converted == False)
        
        if conversion_status:
            query = query.filter(Conversion.status == conversion_status)
        
        if date_from:
            try:
                # HTML date input returns YYYY-MM-DD format
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(AffiliateClick.created_at >= from_date)
            except (ValueError, TypeError):
                pass  # Invalid date, ignore filter
        
        if date_to:
            try:
                # HTML date input returns YYYY-MM-DD format
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the entire end date
                to_date = to_date + timedelta(days=1)
                query = query.filter(AffiliateClick.created_at < to_date)
            except (ValueError, TypeError):
                pass  # Invalid date, ignore filter
        
        if url_search:
            query = query.filter(AffiliateClick.url.ilike(f'%{url_search}%'))
        
        # Apply sorting
        if sort_by == 'created_at':
            order_column = AffiliateClick.created_at
        elif sort_by == 'converted_at':
            order_column = AffiliateClick.converted_at
        elif sort_by == 'has_converted':
            order_column = AffiliateClick.has_converted
        elif sort_by == 'user_email':
            order_column = User.email
        elif sort_by == 'user_display_name':
            order_column = User.display_name
        elif sort_by == 'product_name':
            order_column = Product.name
        elif sort_by == 'list_title':
            order_column = List.title
        elif sort_by == 'retailer_name':
            order_column = Retailer.name
        elif sort_by == 'conversion_revenue':
            order_column = Conversion.revenue
        elif sort_by == 'conversion_commission':
            order_column = Conversion.commission
        elif sort_by == 'conversion_status':
            order_column = Conversion.status
        else:
            order_column = AffiliateClick.created_at
        
        # Apply sort order
        if sort_order == 'asc':
            query = query.order_by(nullslast(order_column.asc()))
        else:
            query = query.order_by(nullslast(order_column.desc()))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Build response data
        clicks_data = []
        for click, user, product, list_obj, product_link, retailer, conversion in pagination.items:
            click_dict = {
                'id': str(click.id),
                'url': click.url,
                'has_converted': click.has_converted,
                'created_at': click.created_at.isoformat() if click.created_at else None,
                'converted_at': click.converted_at.isoformat() if click.converted_at else None,
                'session_id': click.session_id,
                'ip_address': click.ip_address,
                'user_agent': click.user_agent,
                'referrer': click.referrer,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'display_name': user.display_name
                } if user else None,
                'product': {
                    'id': str(product.id),
                    'name': product.name,
                    'image_url': product.image_url
                } if product else None,
                'list': {
                    'id': str(list_obj.id),
                    'title': list_obj.title,
                    'slug': list_obj.slug
                } if list_obj else None,
                'product_link': {
                    'id': str(product_link.id),
                    'url': product_link.url,
                    'link_name': product_link.link_name,
                    'price': float(product_link.price) if product_link.price else None
                } if product_link else None,
                'retailer': {
                    'id': str(retailer.id),
                    'name': retailer.name,
                    'logo_url': retailer.logo_url
                } if retailer else None,
                'conversion': {
                    'id': str(conversion.id),
                    'revenue': float(conversion.revenue) if conversion.revenue else None,
                    'commission': float(conversion.commission) if conversion.commission else None,
                    'status': conversion.status,
                    'converted_at': conversion.converted_at.isoformat() if conversion.converted_at else None
                } if conversion else None
            }
            clicks_data.append(click_dict)
        
        return jsonify({
            'clicks': clicks_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        import traceback
        print(f"Error fetching affiliate clicks: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/conversions', methods=['GET'])
@require_admin
def get_admin_conversions(current_user):
    """Get all conversions with pagination and joined data"""
    try:
        # Get query parameters for pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get sort parameters
        sort_by = request.args.get('sort_by', 'converted_at').strip()
        sort_order = request.args.get('sort_order', 'desc').strip().lower()
        
        # Validate sort parameters
        valid_sort_columns = [
            'converted_at', 'created_at', 'revenue', 'commission', 
            'status', 'network', 'list_title', 'product_name'
        ]
        if sort_by not in valid_sort_columns:
            sort_by = 'converted_at'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Get filter parameters
        status = request.args.get('status', '').strip()
        network = request.args.get('network', '').strip()
        list_search = request.args.get('list_search', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        
        # Build query with joins
        query = db.session.query(
            Conversion,
            List,
            Product,
            AffiliateClick,
            User
        ).join(
            List, Conversion.list_id == List.id
        ).outerjoin(
            Product, Conversion.product_id == Product.id
        ).outerjoin(
            AffiliateClick, Conversion.click_id == AffiliateClick.id
        ).outerjoin(
            User, AffiliateClick.user_id == User.id
        )
        
        # Apply filters
        if status and status != '__all__':
            query = query.filter(Conversion.status == status)
            
        if network and network != '__all__':
            query = query.filter(Conversion.network == network)
            
        if list_search:
            query = query.filter(List.title.ilike(f'%{list_search}%'))
            
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Conversion.converted_at >= from_date)
            except (ValueError, TypeError):
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Conversion.converted_at < to_date)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        if sort_by == 'converted_at':
            order_column = Conversion.converted_at
        elif sort_by == 'created_at':
            order_column = Conversion.created_at
        elif sort_by == 'revenue':
            order_column = Conversion.revenue
        elif sort_by == 'commission':
            order_column = Conversion.commission
        elif sort_by == 'status':
            order_column = Conversion.status
        elif sort_by == 'network':
            order_column = Conversion.network
        elif sort_by == 'list_title':
            order_column = List.title
        elif sort_by == 'product_name':
            order_column = Product.name
        else:
            order_column = Conversion.converted_at
            
        # Apply sort order
        if sort_order == 'asc':
            query = query.order_by(nullslast(order_column.asc()))
        else:
            query = query.order_by(nullslast(order_column.desc()))
            
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Build response data
        conversions_data = []
        for conv, list_obj, product, click, user in pagination.items:
            conv_dict = conv.to_dict()
            
            # Add related data
            conv_dict['list'] = {
                'id': str(list_obj.id),
                'title': list_obj.title,
                'slug': list_obj.slug
            }
            
            if product:
                conv_dict['product'] = {
                    'id': str(product.id),
                    'name': product.name,
                    'image_url': product.image_url
                }
                
            if click:
                conv_dict['click'] = {
                    'id': str(click.id),
                    'url': click.url,
                    'created_at': click.created_at.isoformat()
                }
                if user:
                    conv_dict['user'] = {
                        'id': str(user.id),
                        'display_name': user.display_name,
                        'email': user.email
                    }
            
            conversions_data.append(conv_dict)
            
        return jsonify({
            'conversions': conversions_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        import traceback
        print(f"Error fetching admin conversions: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
