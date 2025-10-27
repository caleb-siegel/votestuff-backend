"""
Product model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Product(db.Model):
    """Product model within lists"""
    __tablename__ = 'products'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    
    # Affiliate links
    affiliate_url = db.Column(db.String(500), nullable=False)
    product_url = db.Column(db.String(500), nullable=True)  # Original product page
    
    # Additional affiliate links (JSON field for multiple sources)
    additional_links = db.Column(db.Text, nullable=True)  # JSON string: {source: url}
    
    # Foreign keys
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    
    # Voting
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer, default=0)
    
    # Analytics
    click_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('Vote', backref='product', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='product', lazy=True, cascade='all, delete-orphan')
    product_links = db.relationship('ProductLink', backref='product', lazy=True, cascade='all, delete-orphan')
    affiliate_clicks = db.relationship('AffiliateClick', backref='product', lazy=True)
    conversions = db.relationship('Conversion', backref='product', lazy=True)
    
    @property
    def net_score(self):
        """Calculate net voting score"""
        return self.upvotes - self.downvotes
    
    @property
    def upvote_percentage(self):
        """Calculate percentage of upvotes"""
        total = self.upvotes + self.downvotes
        if total == 0:
            return 0
        return (self.upvotes / total) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'affiliate_url': self.affiliate_url,
            'product_url': self.product_url,
            'list_id': str(self.list_id),
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'net_score': self.net_score,
            'upvote_percentage': round(self.upvote_percentage, 2),
            'rank': self.rank,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

