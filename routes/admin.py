"""
Admin routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, List, Product, ProductLink, User, ContactSubmission, Payout, Category, Retailer, AffiliateClick, Conversion, Vote
from utils.auth_decorators import require_admin
from datetime import datetime, timedelta
from sqlalchemy import func, desc
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
        lst = List.query.get_or_404(uuid.UUID(list_id))
        
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
        lst = List.query.get_or_404(uuid.UUID(list_id))
        
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
        lst = List.query.get_or_404(uuid.UUID(list_id))
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
        
        # Recent conversions
        recent_conversions_query = Conversion.query.order_by(desc(Conversion.converted_at)).limit(10).all()
        recent_conversions_data = [conv.to_dict() for conv in recent_conversions_query]
        
        # Daily clicks and conversions for the last 30 days
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
            
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'clicks': day_clicks,
                'conversions': day_conversions
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

