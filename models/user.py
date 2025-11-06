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
    
    def get_cashback_stats(self):
        """Calculate cashback statistics from conversions and payouts"""
        from .payout import Payout
        
        # Get total cashback earned (from paid cashback payouts)
        total_cashback_earned = db.session.query(
            db.func.sum(Payout.amount)
        ).filter(
            Payout.user_id == self.id,
            Payout.payout_type == 'cashback',
            Payout.status == 'paid'
        ).scalar() or 0
        
        # Get pending cashback (from pending/approved cashback payouts)
        pending_cashback = db.session.query(
            db.func.sum(Payout.amount)
        ).filter(
            Payout.user_id == self.id,
            Payout.payout_type == 'cashback',
            Payout.status.in_(['pending', 'processing'])
        ).scalar() or 0
        
        return {
            'current_balance': float(self.cashback_balance) if self.cashback_balance else 0,
            'total_earned': float(total_cashback_earned) if total_cashback_earned else 0,
            'pending_amount': float(pending_cashback) if pending_cashback else 0,
            'total_paid_out': float(self.total_payout) if self.total_payout else 0
        }
    
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

