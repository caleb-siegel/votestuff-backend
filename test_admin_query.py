from app import app
from models import db, Conversion, List, Product, AffiliateClick, User
from sqlalchemy import desc, outerjoin, nullslast

with app.app_context():
    print("Testing admin conversions query...")
    
    # Replicating the query from admin.py
    query = db.session.query(
        Conversion,
        List,
        Product,
        AffiliateClick,
        User
    ).join(
        List, Conversion.list_id == List.id
    ).outerjoin(
        Product, Conversion.product_id == Product.id
    ).outerjoin(
        AffiliateClick, Conversion.click_id == AffiliateClick.id
    ).outerjoin(
        User, AffiliateClick.user_id == User.id
    )
    
    # Apply default sorting
    query = query.order_by(nullslast(Conversion.converted_at.desc()))
    
    # Get results
    results = query.limit(10).all()
    
    print(f"Found {len(results)} results")
    
    found_manual = False
    for row in results:
        conv, lst, prod, click, user = row
        print(f"Conv ID: {conv.id}, Status: {conv.status}, Network: {conv.network}")
        if conv.network == 'manual':
            found_manual = True
            print("  -> FOUND MANUAL CONVERSION")
            print(f"  List: {lst.title if lst else 'None'}")
            print(f"  Product: {prod.name if prod else 'None'}")
            print(f"  Click: {click.id if click else 'None'}")
            print(f"  User: {user.email if user else 'None'}")
            
    if not found_manual:
        print("MANUAL CONVERSION NOT FOUND IN QUERY RESULTS")
