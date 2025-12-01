"""
Share routes for social media optimization
"""

from flask import Blueprint, redirect, render_template_string, current_app
from models import List, Product
import uuid
from sqlalchemy.orm import joinedload

share_bp = Blueprint('share', __name__)

@share_bp.route('/share/list/<list_id>')
def share_list(list_id):
    """
    Serve a page with Open Graph tags for a list, then redirect to the frontend.
    """
    try:
        # Fetch list with products to get the top image
        lst = List.query.options(
            joinedload(List.products)
        ).get_or_404(uuid.UUID(list_id))
        
        # Determine the image to show
        # 1. Top ranked product image
        # 2. List category icon (if we had a way to map it to an image)
        # 3. Default logo
        
        og_image = "https://votestuff.com/logo.png" # Default
        
        if lst.products:
            # Sort by rank to find the top product
            sorted_products = sorted(lst.products, key=lambda p: p.rank if p.rank else 999)
            if sorted_products and sorted_products[0].image_url:
                og_image = sorted_products[0].image_url
        
        # Construct frontend URL
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        target_url = f"{frontend_url}/list/{list_id}"
        
        # HTML template with meta tags and redirect
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{lst.title} - VoteStuff</title>
            <meta property="og:title" content="{lst.title} - VoteStuff" />
            <meta property="og:description" content="{lst.description or 'Check out this list on VoteStuff!'}" />
            <meta property="og:image" content="{og_image}" />
            <meta property="og:url" content="{target_url}" />
            <meta property="og:type" content="website" />
            
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="{lst.title} - VoteStuff" />
            <meta name="twitter:description" content="{lst.description or 'Check out this list on VoteStuff!'}" />
            <meta name="twitter:image" content="{og_image}" />
            
            <script>
                window.location.href = "{target_url}";
            </script>
        </head>
        <body>
            <p>Redirecting to <a href="{target_url}">{lst.title}</a>...</p>
        </body>
        </html>
        """
        
        return render_template_string(html)
        
    except ValueError:
        return "Invalid List ID", 400
    except Exception as e:
        print(f"Error serving share page: {e}")
        return "Error", 500
