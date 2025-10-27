"""
Analytics routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, AffiliateClick, Conversion, Payout
from sqlalchemy import desc

@api_bp.route('/analytics/clicks', methods=['GET'])
def get_click_analytics():
    """Get click analytics"""
    # TODO: Add authentication and authorization checks
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AffiliateClick.query
    
    if start_date and end_date:
        query = query.filter(
            AffiliateClick.created_at >= start_date,
            AffiliateClick.created_at <= end_date
        )
    
    clicks = query.order_by(desc(AffiliateClick.created_at)).all()
    
    return jsonify({
        'clicks': [click.to_dict() for click in clicks],
        'total': len(clicks)
    })

@api_bp.route('/analytics/conversions', methods=['GET'])
def get_conversion_analytics():
    """Get conversion analytics"""
    # TODO: Add authentication and authorization checks
    conversions = Conversion.query.order_by(desc(Conversion.converted_at)).all()
    
    total_revenue = sum(float(conv.revenue) if conv.revenue else 0 for conv in conversions)
    total_commission = sum(float(conv.commission) if conv.commission else 0 for conv in conversions)
    
    return jsonify({
        'conversions': [conv.to_dict() for conv in conversions],
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'count': len(conversions)
    })

