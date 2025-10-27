"""
Database models for VoteStuff
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import all models (done after db initialization to avoid circular imports)
__all__ = [
    'db',
    'User',
    'Category',
    'List',
    'Product',
    'Vote',
    'Wishlist',
    'Retailer',
    'ProductLink',
    'AffiliateClick',
    'Conversion',
    'Payout',
    'ContactSubmission'
]

# Import all models after db is initialized
from .user import User
from .category import Category
from .list import List
from .product import Product
from .vote import Vote
from .wishlist import Wishlist
from .retailer import Retailer
from .product_link import ProductLink
from .affiliate_click import AffiliateClick
from .conversion import Conversion
from .payout import Payout
from .contact_submission import ContactSubmission

