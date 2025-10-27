"""
Payout model for creators
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Payout(db.Model):
    """Payout tracking for list creators"""
    __tablename__ = 'payouts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    conversion_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversions.id'), nullable=True)
    
    # Payout details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, processing, paid, failed
    currency = db.Column(db.String(10), default='USD')
    
    # Payment method
    payment_method = db.Column(db.String(50), nullable=True)  # 'paypal', 'stripe', 'direct_deposit'
    payment_reference = db.Column(db.String(255), nullable=True)
    
    # Admin notes
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'list_id': str(self.list_id),
            'conversion_id': str(self.conversion_id) if self.conversion_id else None,
            'amount': float(self.amount) if self.amount else 0,
            'status': self.status,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }
    
    def __repr__(self):
        return f'<Payout {self.amount} - {self.status}>'

