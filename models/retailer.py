"""
Retailer model for storing affiliate partners and retailers
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Retailer(db.Model):
    """Retailer model for affiliate partners"""
    __tablename__ = 'retailers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Affiliate network information
    affiliate_network = db.Column(db.String(200), nullable=True)  # e.g., "Amazon Associates", "Impact Radius"
    commission_rate = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage commission (e.g., 4.5)
    base_affiliate_link = db.Column(db.String(500), nullable=True)  # Base affiliate URL/tag
    
    # Display information
    logo_url = db.Column(db.String(500), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product_links = db.relationship('ProductLink', backref='retailer', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'affiliate_network': self.affiliate_network,
            'commission_rate': float(self.commission_rate) if self.commission_rate else None,
            'base_affiliate_link': self.base_affiliate_link,
            'logo_url': self.logo_url,
            'website_url': self.website_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Retailer {self.name}>'

