"""
User model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # None for OAuth users
    display_name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Authentication
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'apple', etc.
    oauth_id = db.Column(db.String(255), nullable=True)
    
    # Financial
    cashback_balance = db.Column(db.Numeric(10, 2), default=0.00)
    total_payout = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lists = db.relationship('List', backref='creator', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    payouts = db.relationship('Payout', backref='user', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'display_name': self.display_name,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'is_admin': self.is_admin,
            'cashback_balance': float(self.cashback_balance) if self.cashback_balance else 0,
            'total_payout': float(self.total_payout) if self.total_payout else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.display_name}>'

