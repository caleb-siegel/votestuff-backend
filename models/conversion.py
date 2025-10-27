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
    
    # Conversion data
    revenue = db.Column(db.Numeric(10, 2), nullable=True)
    commission = db.Column(db.Numeric(10, 2), nullable=True)
    commission_rate = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage
    currency = db.Column(db.String(10), default='USD')
    
    # Affiliate network
    network = db.Column(db.String(50), nullable=True)  # 'amazon', 'impact', 'partnerize'
    external_id = db.Column(db.String(255), nullable=True)  # External conversion ID
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    converted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    payout = db.relationship('Payout', backref='conversion', uselist=False, lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'click_id': str(self.click_id) if self.click_id else None,
            'list_id': str(self.list_id),
            'product_id': str(self.product_id),
            'revenue': float(self.revenue) if self.revenue else 0,
            'commission': float(self.commission) if self.commission else 0,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0,
            'currency': self.currency,
            'network': self.network,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None
        }
    
    def __repr__(self):
        return f'<Conversion {self.id}>'

