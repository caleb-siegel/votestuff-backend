"""
Category model
"""

from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Category(db.Model):
    """Category model for organizing lists"""
    __tablename__ = 'categories'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)  # Icon name/emoji
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=True, default=None)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lists = db.relationship('List', backref='category', lazy=True)
    parent = db.relationship('Category', remote_side=[id], backref='children')
    
    def to_dict(self, include_children=False, count_dict=None):
        """Convert to dictionary"""
        cat_id_str = str(self.id)
        # Use provided count_dict if available (much faster), otherwise fall back to len
        if count_dict is not None:
            list_count = count_dict.get(cat_id_str, 0)
        else:
            # Fallback: use database count query instead of loading all lists
            from sqlalchemy import func
            from models.list import List
            list_count = db.session.query(func.count(List.id)).filter(
                List.category_id == self.id,
                List.status == 'approved'
            ).scalar() or 0
        
        result = {
            'id': cat_id_str,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'list_count': list_count
        }
        if include_children:
            result['children'] = [child.to_dict(include_children=True, count_dict=count_dict) for child in self.children]
        return result
    
    def __repr__(self):
        return f'<Category {self.name}>'

