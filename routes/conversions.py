"""
Conversion and cashback routes
"""

from flask import request, jsonify
from . import api_bp
from models import (
    db, Conversion, AffiliateClick, 
    User, Product, List, Payout
)
from datetime import datetime, timedelta
from decimal import Decimal
from config import Config
import uuid

# Configuration for cashback and creator payout percentages
# These can be configured via environment variables in config.py
DEFAULT_CASHBACK_PERCENTAGE = Decimal(str(Config.CASHBACK_PERCENTAGE))  # % of commission to user
DEFAULT_CREATOR_PAYOUT_PERCENTAGE = Decimal(str(Config.CREATOR_PAYOUT_PERCENTAGE))  # % of commission to creator
# Remaining percentage stays with platform

@api_bp.route('/conversions/webhook', methods=['POST'])
def conversion_webhook():
    """
    Webhook endpoint to receive conversion notifications from affiliate networks
    
    The conversion is about the PURCHASE event. We then match it to clicks for attribution.
    
    Expected payload structure (adjust based on your affiliate network):
    {
        "external_id": "conversion_id_from_network",
        "network": "amazon|impact|partnerize",
        "revenue": 100.00,
        "commission": 5.00,
        "commission_rate": 5.0,
        "currency": "USD",
        "converted_at": "2024-01-01T00:00:00Z",
        "product_id": "uuid",
        "list_id": "uuid",
        "purchaser_id": "uuid",  # Optional: user_id if affiliate network identifies user
        "purchaser_email": "email@example.com",  # Optional: email to match user
        "click_id": "uuid"  # Optional: if affiliate network tracks click_id
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Required fields
        external_id = data.get('external_id')
        network = data.get('network', 'unknown')
        revenue = data.get('revenue')
        commission = data.get('commission')
        
        if not external_id or revenue is None or commission is None:
            return jsonify({'error': 'Missing required fields: external_id, revenue, commission'}), 400
        
        # Try to find existing conversion by external_id
        existing_conversion = Conversion.query.filter_by(
            external_id=external_id,
            network=network
        ).first()
        
        if existing_conversion:
            return jsonify({
                'message': 'Conversion already processed',
                'conversion_id': str(existing_conversion.id)
            }), 200
        
        # Get product and list info
        product_id = data.get('product_id')
        list_id = data.get('list_id')
        
        if not product_id or not list_id:
            return jsonify({'error': 'Missing product_id or list_id'}), 400
        
        try:
            product_id = uuid.UUID(product_id)
            list_id = uuid.UUID(list_id)
        except ValueError:
            return jsonify({'error': 'Invalid product_id or list_id format'}), 400
        
        product = Product.query.get(product_id)
        lst = List.query.get(list_id)
        
        if not product or not lst:
            return jsonify({'error': 'Product or list not found'}), 404
        
        # Identify purchaser from webhook data
        purchaser_id = None
        
        # Try to get purchaser_id directly from webhook
        purchaser_id_param = data.get('purchaser_id')
        if purchaser_id_param:
            try:
                purchaser_id = uuid.UUID(purchaser_id_param)
            except ValueError:
                pass
        
        # If no purchaser_id, try to match by email
        if not purchaser_id:
            purchaser_email = data.get('purchaser_email')
            if purchaser_email:
                purchaser = User.query.filter_by(email=purchaser_email).first()
                if purchaser:
                    purchaser_id = purchaser.id
        
        # Now try to find the click that led to this conversion for attribution
        click_id = data.get('click_id')
        click = None
        clicker_user_id = None  # User who clicked (may be different from purchaser)
        
        # Try to get click from webhook click_id
        if click_id:
            try:
                click = AffiliateClick.query.get(uuid.UUID(click_id))
            except ValueError:
                pass
        
        # If no click_id provided, try to match by product/list and purchaser/time window
        if not click:
            # Look for recent clicks on this product/list
            # Match by purchaser_id if available, otherwise by time window
            
            query = AffiliateClick.query.filter(
                AffiliateClick.product_id == product_id,
                AffiliateClick.list_id == list_id,
                AffiliateClick.has_converted == False
            )
            
            # If we have purchaser_id, try to match clicks by that user
            if purchaser_id:
                query = query.filter(AffiliateClick.user_id == purchaser_id)
            
            # Only look at clicks within last 30 days (affiliate windows vary)
            time_window = datetime.utcnow() - timedelta(days=30)
            query = query.filter(AffiliateClick.created_at >= time_window)
            
            # Get most recent matching click
            click = query.order_by(AffiliateClick.created_at.desc()).first()
        
        # Get clicker user_id from click (for cashback attribution)
        if click:
            clicker_user_id = click.user_id
            # Mark click as converted
            click.has_converted = True
        
        # Parse timestamps
        converted_at_str = data.get('converted_at')
        converted_at = datetime.utcnow()
        if converted_at_str:
            try:
                converted_at = datetime.fromisoformat(converted_at_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Mark click conversion timestamp if we found one
        if click:
            click.converted_at = converted_at
        
        # Create conversion record - this is the PURCHASE event
        conversion = Conversion(
            id=uuid.uuid4(),
            click_id=click.id if click else None,  # Link to click for attribution
            list_id=list_id,
            product_id=product_id,
            purchaser_id=purchaser_id,  # User who made the purchase
            revenue=Decimal(str(revenue)),
            commission=Decimal(str(commission)),
            commission_rate=Decimal(str(data.get('commission_rate', 0))),
            currency=data.get('currency', 'USD'),
            network=network,
            external_id=external_id,
            converted_at=converted_at,  # When purchase happened
            status='pending',  # Initial status
            # Set payout percentages
            cashback_percentage=DEFAULT_CASHBACK_PERCENTAGE,
            creator_payout_percentage=DEFAULT_CREATOR_PAYOUT_PERCENTAGE
        )
        
        db.session.add(conversion)
        
        # Calculate cashback amount
        cashback_amount = (conversion.commission * conversion.cashback_percentage) / Decimal('100')
        
        # Create cashback payout for the user who clicked (clicker gets cashback)
        # This is the attribution - the clicker gets rewarded, not necessarily the purchaser
        if clicker_user_id:
            cashback_payout = Payout(
                id=uuid.uuid4(),
                user_id=clicker_user_id,  # User who clicked gets cashback
                list_id=list_id,
                conversion_id=conversion.id,
                payout_type='cashback',
                amount=cashback_amount,
                status='pending',
                currency=conversion.currency
            )
            
            db.session.add(cashback_payout)
        
        # Calculate creator payout amount
        creator_payout_amount = (conversion.commission * conversion.creator_payout_percentage) / Decimal('100')
        
        # Create payout record for list creator
        if lst.creator_id:
            creator_payout = Payout(
                id=uuid.uuid4(),
                user_id=lst.creator_id,
                list_id=list_id,
                conversion_id=conversion.id,
                payout_type='creator',
                amount=creator_payout_amount,
                status='pending',
                currency=conversion.currency
            )
            
            db.session.add(creator_payout)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Conversion processed',
            'conversion_id': str(conversion.id),
            'purchaser_id': str(purchaser_id) if purchaser_id else None,
            'clicker_user_id': str(clicker_user_id) if clicker_user_id else None,
            'cashback_amount': float(cashback_amount) if clicker_user_id else None,
            'creator_payout_amount': float(creator_payout_amount) if lst.creator_id else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/conversions/<conversion_id>/approve', methods=['POST'])
def approve_conversion(conversion_id):
    """
    Mark conversion as approved by affiliate network
    Updates conversion status and related payout statuses
    """
    try:
        conversion = Conversion.query.get_or_404(uuid.UUID(conversion_id))
        
        # Update conversion status
        conversion.status = 'approved'
        conversion.approved_at = datetime.utcnow()
        
        # Update related payouts to 'processing' (they're approved but not yet paid)
        payouts = Payout.query.filter_by(
            conversion_id=conversion.id,
            status='pending'
        ).all()
        
        for payout in payouts:
            payout.status = 'processing'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Conversion approved, {len(payouts)} payouts updated'
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid conversion ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/conversions/<conversion_id>/paid', methods=['POST'])
def mark_conversion_paid(conversion_id):
    """
    Mark conversion as paid (commission received from retailer)
    Updates conversion status to 'paid' and updates user balances
    Also processes creator payouts
    """
    try:
        conversion = Conversion.query.get_or_404(uuid.UUID(conversion_id))
        
        # Update conversion status
        conversion.status = 'paid'
        conversion.paid_at = datetime.utcnow()
        
        # Update all payouts for this conversion
        payouts = Payout.query.filter_by(
            conversion_id=conversion.id,
            status='processing'
        ).all()
        
        paid_count = 0
        total_cashback_paid = Decimal('0')
        
        for payout in payouts:
            payout.status = 'paid'
            payout.paid_at = datetime.utcnow()
            
            # Update user balance based on payout type
            user = User.query.get(payout.user_id)
            if user:
                if payout.payout_type == 'cashback':
                    # Update cashback balance
                    user.cashback_balance = (user.cashback_balance or Decimal('0')) + payout.amount
                    total_cashback_paid += payout.amount
                elif payout.payout_type == 'creator':
                    # Update creator's total payout
                    user.total_payout = (user.total_payout or Decimal('0')) + payout.amount
            
            paid_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Conversion marked as paid, {paid_count} payouts processed',
            'total_cashback_paid': float(total_cashback_paid)
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid conversion ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
