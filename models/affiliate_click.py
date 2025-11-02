"""
Affiliate Click tracking model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AffiliateClick(db.Model):
    """Track affiliate link clicks"""
    __tablename__ = 'affiliate_clicks'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    product_link_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_links.id'), nullable=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # Null for guests
    
    # Click tracking
    url = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    
    # Conversion tracking
    has_converted = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    converted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    conversion = db.relationship('Conversion', backref='click', uselist=False, lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'list_id': str(self.list_id),
            'product_id': str(self.product_id),
            'product_link_id': str(self.product_link_id) if self.product_link_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'url': self.url,
            'has_converted': self.has_converted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None
        }
    
    def __repr__(self):
        return f'<AffiliateClick {self.url}>'

