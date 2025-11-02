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
    image_url = db.Column(db.Text, nullable=True)
    
    # Affiliate links
    affiliate_url = db.Column(db.Text, nullable=False)
    product_url = db.Column(db.Text, nullable=True)  # Original product page
    
    # Additional affiliate links (JSON field for multiple sources)
    additional_links = db.Column(db.Text, nullable=True)  # JSON string: {source: url}
    
    # Foreign keys
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    retailer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('retailers.id'), nullable=True)
    
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
    retailer = db.relationship('Retailer', backref='products', lazy=True)
    votes = db.relationship('Vote', backref='product', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='product', lazy=True, cascade='all, delete-orphan')
    product_links = db.relationship('ProductLink', backref='product', lazy=True, cascade='all, delete-orphan')
    affiliate_clicks = db.relationship('AffiliateClick', backref='product', lazy=True)
    conversions = db.relationship('Conversion', backref='product', lazy=True)
    
    @property
    def net_score(self):
        """
        Calculate net voting score (PRIMARY RANKING FACTOR)
        
        This is the most important metric for ranking products within a list.
        Net score = upvotes - downvotes
        
        Examples:
        - Product A: 10 upvotes, 2 downvotes = net score of 8
        - Product B: 5 upvotes, 0 downvotes = net score of 5
        - Product C: 3 upvotes, 5 downvotes = net score of -2
        
        In ranking: Product A (8) > Product B (5) > Product C (-2)
        
        This property is used by update_list_ranking() to determine product order.
        """
        return self.upvotes - self.downvotes
    
    @property
    def upvote_percentage(self):
        """
        Calculate percentage of total votes that are upvotes (SECONDARY RANKING FACTOR)
        
        This metric helps break ties when products have the same net score.
        It indicates the consistency of positive sentiment.
        
        Formula: (upvotes / total_votes) * 100
        
        Examples:
        - Product A: 8 upvotes, 2 downvotes = 80% upvote (8/10 * 100)
        - Product B: 4 upvotes, 1 downvote = 80% upvote (4/5 * 100)
        - Product C: 40 upvotes, 10 downvotes = 80% upvote (40/50 * 100)
        
        If Products A, B, and C all have the same net score (+6), they would be tied.
        In that case, upvote percentage wouldn't help (all 80%), and the system
        would use the tertiary factor: most recent upvote timestamp.
        
        If net scores are equal but percentages differ:
        - Product A: +6 net, 80% upvote
        - Product D: +6 net, 85% upvote
        Product D would rank higher due to better upvote percentage.
        
        Returns 0 if there are no votes yet (to avoid division by zero).
        
        This property is used by update_list_ranking() as the secondary sorting criterion.
        """
        total = self.upvotes + self.downvotes
        if total == 0:
            return 0
        return (self.upvotes / total) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        # Include product links if they exist
        product_links_data = []
        if hasattr(self, 'product_links'):
            product_links_data = [link.to_dict() for link in self.product_links]
        
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'affiliate_url': self.affiliate_url,
            'product_url': self.product_url,
            'list_id': str(self.list_id),
            'retailer_id': str(self.retailer_id) if self.retailer_id else None,
            'retailer': self.retailer.to_dict() if self.retailer else None,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'net_score': self.net_score,
            'upvote_percentage': round(self.upvote_percentage, 2),
            'rank': self.rank,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'product_links': product_links_data
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

