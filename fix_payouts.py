
from app import create_app
from models import db, User, List, Payout, Conversion, AffiliateClick
import uuid
from datetime import datetime

app = create_app()

def backfill_payouts():
    with app.app_context():
        # Find conversions without payouts
        # We need to check if a Conversion has any associated Payout of type 'creator'
        
        all_conversions = Conversion.query.all()
        print(f"Found {len(all_conversions)} total conversions.")
        
        fixed_count = 0
        
        for conversion in all_conversions:
            # Check if creator payout exists
            existing_payout = Payout.query.filter_by(
                conversion_id=conversion.id,
                payout_type='creator'
            ).first()
            
            if not existing_payout:
                print(f"Missing creator payout for Conversion {conversion.id}")
                
                # Get the list to find the creator
                lst = List.query.get(conversion.list_id)
                if not lst or not lst.creator_id:
                    print(f"  Skipping: List or creator not found for List {conversion.list_id}")
                    continue
                    
                # Calculate commission amount
                # Default to 1% if not specified on conversion (just a safe fallback, 
                # but ideally conversion.commission is set)
                amount = conversion.commission
                if not amount and conversion.revenue:
                     # Fallback calculation if commission is missing on conversion but revenue exists
                     # Assuming standard 1% for now if data is missing
                     amount = float(conversion.revenue) * 0.01
                
                if not amount:
                    print("  Skipping: No commission amount determinable")
                    continue
                    
                # Create Payout
                payout = Payout(
                    id=uuid.uuid4(),
                    user_id=lst.creator_id,
                    list_id=lst.id,
                    conversion_id=conversion.id,
                    payout_type='creator',
                    amount=amount,
                    status='pending', # Default to pending
                    currency=conversion.currency or 'USD',
                    created_at=datetime.utcnow()
                )
                
                db.session.add(payout)
                print(f"  Created Payout for ${amount} for User {lst.creator_id}")
                fixed_count += 1
                
        if fixed_count > 0:
            db.session.commit()
            print(f"\nSuccessfully backfilled {fixed_count} payouts.")
        else:
            print("\nNo missing payouts found or backfilled.")

if __name__ == '__main__':
    backfill_payouts()
