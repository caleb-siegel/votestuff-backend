"""
Vote model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Vote(db.Model):
    """Vote model for products"""
    __tablename__ = 'votes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    list_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lists.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # Null for guests
    
    # Voting
    vote_type = db.Column(db.String(10), nullable=False)  # 'up' or 'down'
    
    # Session tracking for anonymous users
    session_id = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one vote per user/product combination
    __table_args__ = (
        db.UniqueConstraint('product_id', 'user_id', name='unique_user_product_vote'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'list_id': str(self.list_id),
            'user_id': str(self.user_id) if self.user_id else None,
            'vote_type': self.vote_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Vote {self.vote_type}>'

