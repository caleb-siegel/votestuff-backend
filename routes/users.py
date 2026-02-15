"""
User routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, User, List, Payout, Conversion, AffiliateClick
from sqlalchemy import desc, or_
from datetime import datetime
import uuid

@api_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        user_data = user.to_dict()
        
        # Add related data
        user_data['lists_created'] = [lst.to_dict() for lst in user.lists]
        user_data['lists_count'] = len(user.lists)
        
        return jsonify(user_data)
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400

@api_bp.route('/users/<user_id>/update', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        data = request.get_json()
        
        # Update allowed fields
        if 'display_name' in data:
            user.display_name = data.get('display_name')
        if 'bio' in data:
            user.bio = data.get('bio')
        if 'profile_picture' in data:
            user.profile_picture = data.get('profile_picture')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated',
            'user': user.to_dict()
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>/cashback/stats', methods=['GET'])
def get_cashback_stats(user_id):
    """Get user cashback statistics"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        stats = user.get_cashback_stats()
        
        return jsonify(stats)
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400

@api_bp.route('/users/<user_id>/cashback/transactions', methods=['GET'])
def get_cashback_transactions(user_id):
    """Get user cashback transaction history (from conversions they made)"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        # Get query parameters
        status = request.args.get('status')  # Filter by conversion status: pending, approved, paid, cancelled
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query - get conversions where this user purchased OR clicked (for cashback)
        # We check both purchaser_id and payouts to find all relevant conversions
        
        # Get conversions where user is purchaser
        purchaser_conversions = Conversion.query.filter_by(purchaser_id=user.id)
        
        # Get conversions where user has cashback payouts (they clicked)
        cashback_payouts = Payout.query.filter_by(
            user_id=user.id,
            payout_type='cashback'
        ).all()
        cashback_conversion_ids = [p.conversion_id for p in cashback_payouts if p.conversion_id]
        
        # Combine both queries
        if cashback_conversion_ids:
            query = Conversion.query.filter(
                or_(
                    Conversion.purchaser_id == user.id,
                    Conversion.id.in_(cashback_conversion_ids)
                )
            )
        else:
            query = purchaser_conversions
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by created_at descending (most recent first)
        query = query.order_by(desc(Conversion.created_at))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        conversions = query.limit(limit).offset(offset).all()
        
        # Get related payouts for each conversion
        conversion_data = []
        for conv in conversions:
            conv_dict = conv.to_dict()
            
            # Get the cashback payout for this conversion
            cashback_payout = Payout.query.filter_by(
                conversion_id=conv.id,
                payout_type='cashback',
                user_id=user.id
            ).first()
            
            if cashback_payout:
                conv_dict['cashback_payout'] = cashback_payout.to_dict()
            
            conversion_data.append(conv_dict)
        
        return jsonify({
            'transactions': conversion_data,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>/cashback/transactions/<transaction_id>', methods=['GET'])
def get_cashback_transaction(user_id, transaction_id):
    """Get single cashback transaction details (conversion)"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        conversion_id = uuid.UUID(transaction_id)
        
        # Check if user is purchaser or has cashback payout for this conversion
        conversion = Conversion.query.filter(
            (Conversion.id == conversion_id) & (
                (Conversion.purchaser_id == user.id) |
                (Conversion.id.in_(
                    db.session.query(Payout.conversion_id).filter_by(
                        user_id=user.id,
                        payout_type='cashback'
                    )
                ))
            )
        ).first_or_404()
        
        conv_dict = conversion.to_dict()
        
        # Get the cashback payout for this conversion
        cashback_payout = Payout.query.filter_by(
            conversion_id=conversion.id,
            payout_type='cashback',
            user_id=user.id
        ).first()
        
        if cashback_payout:
            conv_dict['cashback_payout'] = cashback_payout.to_dict()
        
        return jsonify(conv_dict)
    except ValueError:
        return jsonify({'error': 'Invalid user ID or transaction ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/users/<user_id>/dashboard', methods=['GET'])
def get_user_dashboard(user_id):
    """Get user dashboard stats for list creators"""
    try:
        user = User.query.get_or_404(uuid.UUID(user_id))
        
        # Get all lists created by user
        user_lists = List.query.filter_by(creator_id=user.id).order_by(desc(List.created_at)).all()
        
        lists_data = []
        total_views = 0
        total_clicks = 0
        total_conversions = 0
        total_revenue = 0
        total_earnings = 0
        pending_earnings = 0
        paid_earnings = 0
        
        for lst in user_lists:
            # Get stats for this list
            # Clicks
            clicks_count = db.session.query(db.func.count(AffiliateClick.id)).filter(
                AffiliateClick.list_id == lst.id
            ).scalar() or 0
            
            # Conversions
            # Calculate count and total revenue
            conversions_data = db.session.query(
                db.func.count(Conversion.id),
                db.func.sum(Conversion.revenue)
            ).filter(
                Conversion.list_id == lst.id
            ).first()
            
            conversions_count = conversions_data[0] or 0
            list_revenue = float(conversions_data[1]) if conversions_data[1] else 0.0
            
            # Commission (Payouts for creator)
            payouts = Payout.query.filter_by(
                list_id=lst.id,
                payout_type='creator'
            ).all()
            
            list_earnings = sum(float(p.amount) for p in payouts)
            list_pending = sum(float(p.amount) for p in payouts if p.status == 'pending')
            list_processing = sum(float(p.amount) for p in payouts if p.status == 'processing')
            list_paid = sum(float(p.amount) for p in payouts if p.status == 'paid')
            list_failed = sum(float(p.amount) for p in payouts if p.status in ['failed', 'cancelled'])
            
            # Add to totals
            total_views += lst.view_count
            total_clicks += clicks_count
            total_conversions += conversions_count
            total_revenue += list_revenue
            total_earnings += list_earnings
            pending_earnings += list_pending
            
            # Add list data
            lists_data.append({
                'id': str(lst.id),
                'title': lst.title,
                'slug': lst.slug,
                'status': lst.status,
                'created_at': lst.created_at.isoformat(),
                'view_count': lst.view_count,
                'click_count': clicks_count,
                'conversion_count': conversions_count,
                'revenue': list_revenue,
                'earnings': list_earnings,
                'pending_earnings': list_pending,
                'paid_earnings': list_paid,
                'product_count': len(lst.products) if lst.products else 0
            })
            
        # Chart Data: Performance History (Daily Stats for last 30 days)
        # ... (Previous code for performance history) ...
        from datetime import timedelta
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=29)
        
        # Initialize daily stats structure
        # Format: [{'date': 'YYYY-MM-DD', 'list_id_clicks': 0, 'list_id_conversions': 0, 'list_id_commission': 0, ...}]
        performance_history = []
        date_map = {}
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            entry = {'date': date_str}
            # Initialize all lists to 0
            for lst in user_lists:
                lid = str(lst.id)
                entry[f"{lid}_clicks"] = 0
                entry[f"{lid}_conversions"] = 0
                entry[f"{lid}_commission"] = 0
            performance_history.append(entry)
            date_map[date_str] = entry
            current_date += timedelta(days=1)
            
        list_ids = [lst.id for lst in user_lists]
        if list_ids:
            # 1. Query Daily Clicks
            clicks_daily = db.session.query(
                db.func.date(AffiliateClick.created_at).label('date'),
                AffiliateClick.list_id,
                db.func.count(AffiliateClick.id)
            ).filter(
                AffiliateClick.list_id.in_(list_ids),
                AffiliateClick.created_at >= start_date
            ).group_by(
                db.func.date(AffiliateClick.created_at),
                AffiliateClick.list_id
            ).all()
            
            for date_val, list_id, count in clicks_daily:
                date_str = str(date_val)
                if date_str in date_map:
                    date_map[date_str][f"{str(list_id)}_clicks"] = count

            # 2. Query Daily Conversions
            conversions_daily = db.session.query(
                db.func.date(Conversion.created_at).label('date'),
                Conversion.list_id,
                db.func.count(Conversion.id)
            ).filter(
                Conversion.list_id.in_(list_ids),
                Conversion.created_at >= start_date
            ).group_by(
                db.func.date(Conversion.created_at),
                Conversion.list_id
            ).all()
            
            for date_val, list_id, count in conversions_daily:
                date_str = str(date_val)
                if date_str in date_map:
                    date_map[date_str][f"{str(list_id)}_conversions"] = count

            # 3. Query Daily Commission (Payouts)
            commission_daily = db.session.query(
                db.func.date(Payout.created_at).label('date'),
                Payout.list_id,
                db.func.sum(Payout.amount)
            ).filter(
                Payout.list_id.in_(list_ids),
                Payout.payout_type == 'creator',
                Payout.created_at >= start_date
            ).group_by(
                db.func.date(Payout.created_at),
                Payout.list_id
            ).all()
            
            for date_val, list_id, amount in commission_daily:
                date_str = str(date_val)
                if date_str in date_map:
                     # Convert Decimal to float for JSON serialization
                    date_map[date_str][f"{str(list_id)}_commission"] = float(amount) if amount else 0.0

        # Calculate Aggregated Earnings by Status across all lists
        # We need to sum up payouts for ALL user lists
        all_creator_payouts = Payout.query.filter(
            Payout.list_id.in_(list_ids) if list_ids else False,
            Payout.payout_type == 'creator'
        ).all()
        
        agg_pending = sum(float(p.amount) for p in all_creator_payouts if p.status == 'pending')
        agg_processing = sum(float(p.amount) for p in all_creator_payouts if p.status == 'processing')
        agg_paid = sum(float(p.amount) for p in all_creator_payouts if p.status == 'paid')
        agg_failed = sum(float(p.amount) for p in all_creator_payouts if p.status in ['failed', 'cancelled'])

        # Chart Data: Earnings Breakdown
        earnings_breakdown = [
            {'name': 'Pending', 'value': agg_pending, 'fill': '#fbbf24'},    # amber-400
            {'name': 'Processing', 'value': agg_processing, 'fill': '#3b82f6'}, # blue-500
            {'name': 'Paid', 'value': agg_paid, 'fill': '#22c55e'},         # green-500
            {'name': 'Failed', 'value': agg_failed, 'fill': '#ef4444'},     # red-500
        ]
            
        return jsonify({
            'overview': {
                'total_lists': len(user_lists),
                'total_views': total_views,
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'total_revenue': total_revenue, 
                'total_earnings': total_earnings,
                'pending_earnings': pending_earnings,
                'paid_earnings': paid_earnings, # Leaving strict paid_earnings in overview for quick access
                'currency': 'USD'
            },
            'lists': lists_data,
            'performance_history': performance_history,
            'earnings_breakdown': earnings_breakdown
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
