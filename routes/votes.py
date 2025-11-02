"""
Voting routes
"""

from flask import request, jsonify
from . import api_bp
from models import db, Vote, Product, List
import uuid

def get_client_ip():
    """
    Get the client's real IP address, handling proxies and load balancers.
    Checks X-Forwarded-For header first, then X-Real-IP, then falls back to remote_addr.
    """
    # Check for X-Forwarded-For header (used by proxies/load balancers)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2)
        # The first one is typically the original client IP
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return ip
    
    # Check for X-Real-IP header (used by some proxies)
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    
    # Fall back to remote_addr
    return request.remote_addr

@api_bp.route('/products/<product_id>/vote', methods=['POST'])
def vote_product(product_id):
    """
    Vote on a product (up or down)
    
    This endpoint handles all voting operations:
    - Adding a new upvote or downvote
    - Changing an existing vote (e.g., upvote to downvote)
    - Removing a vote (toggle off)
    
    After each vote operation, the product's upvotes/downvotes counters are updated,
    and then update_list_ranking() is called to recalculate all product ranks within
    the list. This ensures products are always displayed in the correct order based
    on the current voting state.
    """
    data = request.get_json()
    vote_type = data.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    # Require user to be signed in to vote
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'You must be signed in to vote. Please log in or create an account.'}), 401
    
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        
        # Check if user already voted on this product
        # Users can only have one vote per product (enforced by unique constraint)
        existing_vote = Vote.query.filter_by(
            product_id=product.id,
            user_id=user_id
        ).first()
        
        # Check if user wants to toggle off their vote (remove it entirely)
        toggle_off = data.get('toggle_off', False)
        
        if existing_vote:
            # User already voted - handle vote modification
            old_type = existing_vote.vote_type
            
            if toggle_off:
                # User is removing their vote entirely
                # Decrement the appropriate counter
                if old_type == 'up':
                    product.upvotes -= 1
                else:
                    product.downvotes -= 1
                
                # Delete the vote record
                db.session.delete(existing_vote)
            else:
                # User is switching vote types (e.g., changing upvote to downvote)
                # Decrement the old vote type counter and increment the new one
                if old_type == 'up':
                    product.upvotes -= 1
                    product.downvotes += 1
                else:
                    product.downvotes -= 1
                    product.upvotes += 1
                
                # Update the vote record to reflect the new vote type
                existing_vote.vote_type = vote_type
        else:
            # User hasn't voted on this product yet - create new vote
            # Only create if not toggling off (can't toggle off a non-existent vote)
            if not toggle_off:
                new_vote = Vote(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    list_id=product.list_id,
                    user_id=user_id,
                    vote_type=vote_type,
                    session_id=data.get('session_id'),
                    ip_address=get_client_ip()  # Store IP for analytics/audit purposes
                )
                db.session.add(new_vote)
                
                # Update product vote counters
                # These counters are used for quick access and ranking calculations
                if vote_type == 'up':
                    product.upvotes += 1
                else:
                    product.downvotes += 1
        
        db.session.commit()
        
        # CRITICAL: After any vote change, recalculate rankings for all products in the list
        # This ensures products are sorted correctly based on:
        # 1. Net score (upvotes - downvotes)
        # 2. Upvote percentage (if net scores are tied)
        # 3. Most recent upvote timestamp (if both are tied)
        # See update_list_ranking() function below for detailed ranking algorithm
        update_list_ranking(product.list_id)
        
        return jsonify({
            'message': 'Vote recorded',
            'product': product.to_dict()  # Returns product with updated vote counts and new rank
        })
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<product_id>/vote-status', methods=['GET'])
def get_vote_status(product_id):
    """Get vote status for a logged-in user"""
    user_id = request.args.get('user_id')
    
    try:
        product = Product.query.get_or_404(uuid.UUID(product_id))
        
        # Find user's vote (only for logged-in users)
        vote_type = None
        if user_id:
            vote = Vote.query.filter_by(
                product_id=product.id,
                user_id=user_id
            ).first()
            if vote:
                vote_type = vote.vote_type
        
        return jsonify({
            'product_id': str(product.id),
            'user_vote': vote_type,
            'upvotes': product.upvotes,
            'downvotes': product.downvotes,
            'net_score': product.net_score
        })
    except ValueError:
        return jsonify({'error': 'Invalid product ID'}), 400

def update_list_ranking(list_id):
    """
    Update product rankings within a list based on voting data.
    
    This is the core ranking algorithm that determines the order products appear
    in a list. Products are sorted using a three-tier priority system:
    
    RANKING PRIORITY (in order of importance):
    ------------------------------------------
    1. NET SCORE (Primary): upvotes - downvotes
       - Products with higher net scores rank higher
       - Example: Product A (10 up, 2 down = net +8) ranks above Product B (5 up, 0 down = net +5)
    
    2. UPVOTE PERCENTAGE (Secondary - used when net scores are equal):
       - Percentage of total votes that are upvotes
       - Products with higher upvote % rank higher (shows more consistent positive sentiment)
       - Example: Product A (8 up, 2 down = 80% upvote) ranks above Product B (40 up, 10 down = 80% upvote)
                  if they have the same net score
    
    3. MOST RECENT UPVOTE TIMESTAMP (Tertiary - breaks ties):
       - When both net score and upvote % are equal, the product with the most recent upvote wins
       - This promotes fresh/recently validated products
       - Products with no upvotes use datetime.min (oldest possible date) so they rank last
    
    ALGORITHM STEPS:
    ----------------
    1. Fetch all products in the list
    2. For each product, find the most recent upvote timestamp (if any)
    3. Sort products using the three-tier priority system
    4. Assign ranks (1 = highest rank, 2 = second, etc.)
    5. Update the list's total_votes counter (sum of all product votes)
    
    Called after every vote operation to keep rankings current and accurate.
    """
    try:
        from sqlalchemy import func
        from models.vote import Vote
        from datetime import datetime
        
        # STEP 1: Get all products in this list
        products = Product.query.filter_by(list_id=list_id).all()
        
        # STEP 2: Find the most recent upvote timestamp for each product
        # This is needed for the tertiary tie-breaking in the ranking algorithm
        product_most_recent_upvotes = {}
        for product in products:
            # Find the most recent upvote for this product
            most_recent_upvote = Vote.query.filter_by(
                product_id=product.id, 
                vote_type='up'  # Only consider upvotes for recency tie-breaking
            ).order_by(Vote.created_at.desc()).first()
            
            if most_recent_upvote:
                # Store the timestamp of the most recent upvote
                product_most_recent_upvotes[product.id] = most_recent_upvote.created_at
            else:
                # If no upvotes exist, use the oldest possible date so it ranks lower
                product_most_recent_upvotes[product.id] = datetime.min
        
        # STEP 3: Define the sorting key function
        # This implements the three-tier ranking priority system described above
        def sort_key(p):
            """
            Returns a tuple used for sorting: (net_score_desc, upvote_%_desc, recent_timestamp)
            
            Python sorts tuples lexicographically, so:
            - First element (-p.net_score): Higher net scores rank higher (negative because we want descending)
            - Second element (-p.upvote_percentage): Higher percentages rank higher (if net scores tie)
            - Third element (timestamp): More recent timestamps rank higher (if both above tie)
            
            Note: net_score and upvote_percentage use negative values because Python's sorted()
            sorts in ascending order by default, and we want descending order (highest first).
            """
            most_recent = product_most_recent_upvotes.get(p.id, datetime.min)
            # Convert datetime to timestamp (float) for sorting (larger = more recent)
            timestamp = most_recent.timestamp() if most_recent != datetime.min else 0
            return (-p.net_score, -p.upvote_percentage, timestamp)
        
        # STEP 4: Sort products using the ranking algorithm
        sorted_products = sorted(products, key=sort_key)
        
        # STEP 5: Assign ranks to products (rank 1 = highest/best, rank 2 = second, etc.)
        # The rank field is stored on each product and used by the frontend to display order
        for rank, product in enumerate(sorted_products, start=1):
            product.rank = rank
        
        # STEP 6: Update the list's total_votes counter
        # This aggregates all votes across all products in the list for list-level analytics
        lst = List.query.get(list_id)
        if lst:
            lst.total_votes = sum(p.upvotes + p.downvotes for p in products)
        
        # Commit all ranking updates to the database
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating ranking: {e}")
