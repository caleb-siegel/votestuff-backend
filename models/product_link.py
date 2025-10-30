"""
ProductLink model for storing product links from various retailers
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ProductLink(db.Model):
    """ProductLink model for multiple links per product"""
    __tablename__ = 'product_links'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    retailer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('retailers.id'), nullable=False)
    
    # Link information
    link_name = db.Column(db.String(200), nullable=True)  # e.g., "Amazon Prime Deal", "Best Buy Price"
    url = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=True)  # Product price at this retailer
    
    # Link properties
    is_affiliate_link = db.Column(db.Boolean, default=True)  # Whether this is an affiliate link
    is_primary = db.Column(db.Boolean, default=False, index=True)  # Primary/default link
    
    # Analytics
    click_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clicks = db.relationship('AffiliateClick', backref='product_link', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'retailer_id': str(self.retailer_id),
            'link_name': self.link_name,
            'url': self.url,
            'price': float(self.price) if self.price else None,
            'is_affiliate_link': self.is_affiliate_link,
            'is_primary': self.is_primary,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'retailer': self.retailer.to_dict() if self.retailer else None
        }
    
    def __repr__(self):
        return f'<ProductLink {self.link_name or self.url}>'

