from app import app
from models import db, Conversion, List, Payout

with app.app_context():
    print("Checking recent conversions...")
    conversions = Conversion.query.order_by(Conversion.created_at.desc()).limit(5).all()
    
    if not conversions:
        print("No conversions found.")
    
    for c in conversions:
        print(f"ID: {c.id}")
        print(f"Network: {c.network}")
        print(f"Status: {c.status}")
        print(f"List ID: {c.list_id}")
        print(f"Product ID: {c.product_id}")
        print(f"Click ID: {c.click_id}")
        print(f"Created At: {c.created_at}")
        
        # Check if list exists
        lst = List.query.get(c.list_id)
        print(f"List Found: {lst.title if lst else 'NO'}")
        
        print("-" * 20)
