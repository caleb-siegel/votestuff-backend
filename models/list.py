"""
List model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class List(db.Model):
    """List model (listicles)"""
    __tablename__ = 'lists'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    
    # Foreign keys
    creator_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=True)
    
    # Status management
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Analytics
    view_count = db.Column(db.Integer, default=0)
    total_votes = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    products = db.relationship('Product', backref='list', lazy=True, cascade='all, delete-orphan', order_by='Product.rank')
    votes = db.relationship('Vote', backref='list', lazy=True, cascade='all, delete-orphan')
    affiliate_clicks = db.relationship('AffiliateClick', backref='list', lazy=True)
    conversions = db.relationship('Conversion', backref='list', lazy=True)
    payouts = db.relationship('Payout', backref='list', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'slug': self.slug,
            'creator_id': str(self.creator_id),
            'category_id': str(self.category_id) if self.category_id else None,
            'status': self.status,
            'view_count': self.view_count,
            'total_votes': self.total_votes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'product_count': len(self.products) if self.products else 0
        }
    
    def __repr__(self):
        return f'<List {self.title}>'

