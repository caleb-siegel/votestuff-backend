"""
Conversion tracking model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Conversion(db.Model):
    """Track affiliate conversions/purchases"""
    __tablename__ = 'conversions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    click_id = db.Column(UUID(as_uuid=True), db.ForeignKey('affiliate_clicks.id'), nullable=True)
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    purchaser_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # User who made the purchase
    
    # Conversion data
    revenue = db.Column(db.Numeric(10, 2), nullable=True)
    commission = db.Column(db.Numeric(10, 2), nullable=True)
    commission_rate = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage
    currency = db.Column(db.String(10), default='USD')
    
    # Payout percentages (for splitting commission)
    creator_payout_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage of commission to creator
    cashback_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage of commission to user who clicked
    
    # Lifecycle status tracking
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, paid, cancelled
    # pending: Conversion detected, waiting for affiliate approval
    # approved: Affiliate approved the conversion
    # paid: Commission received from retailer
    # cancelled: Transaction cancelled (e.g., refund, invalid conversion)
    
    # Affiliate network
    network = db.Column(db.String(50), nullable=True)  # 'amazon', 'impact', 'partnerize'
    external_id = db.Column(db.String(255), nullable=True)  # External conversion ID
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    converted_at = db.Column(db.DateTime, default=datetime.utcnow)  # When user made purchase
    approved_at = db.Column(db.DateTime, nullable=True)  # When affiliate approved
    paid_at = db.Column(db.DateTime, nullable=True)  # When commission was received
    
    # Relationships
    payouts = db.relationship('Payout', backref='conversion', lazy=True)  # Changed to plural for multiple payouts
    purchaser = db.relationship('User', backref='purchases', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'click_id': str(self.click_id) if self.click_id else None,
            'list_id': str(self.list_id),
            'product_id': str(self.product_id),
            'purchaser_id': str(self.purchaser_id) if self.purchaser_id else None,
            'revenue': float(self.revenue) if self.revenue else 0,
            'commission': float(self.commission) if self.commission else 0,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0,
            'currency': self.currency,
            'creator_payout_percentage': float(self.creator_payout_percentage) if self.creator_payout_percentage else None,
            'cashback_percentage': float(self.cashback_percentage) if self.cashback_percentage else None,
            'status': self.status,
            'network': self.network,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }
    
    def __repr__(self):
        return f'<Conversion {self.id}>'

