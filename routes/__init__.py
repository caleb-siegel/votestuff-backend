"""
API routes for VoteStuff
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import all route modules to register routes
import routes.auth
import routes.lists
import routes.products
import routes.votes
import routes.categories
import routes.users
import routes.wishlist
import routes.contact
import routes.admin
import routes.analytics
import routes.search
import routes.retailers

