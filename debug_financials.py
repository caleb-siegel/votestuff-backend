
from app import create_app
from models import db, User, List, Payout, Conversion
import uuid

app = create_app()

def inspect_financials():
    with app.app_context():
        # Find the test user 'Caleb' or similar
        user = User.query.filter(User.display_name.ilike('%caleb%')).first()
        if not user:
            user = User.query.join(List).first()
            
        print(f"Inspecting financials for user: {user.display_name} ({user.id})")
        
        # Check Conversions
        conversions = Conversion.query.filter(
            Conversion.list_id.in_([l.id for l in user.lists])
        ).all()
        print(f"\nFound {len(conversions)} conversions for user's lists.")
        for c in conversions:
            print(f"  Conversion {c.id}: Amount=${c.revenue}, Comm=${c.commission}, Status={c.status}")
            
        # Check Payouts
        payouts = Payout.query.filter(
            Payout.list_id.in_([l.id for l in user.lists])
        ).all()
        print(f"\nFound {len(payouts)} payouts linked to user's lists.")
        for p in payouts:
            print(f"  Payout {p.id}: Type={p.payout_type}, Amount=${p.amount}, Status={p.status}, UserID={p.user_id}")
            
        # Check specifically for 'creator' payouts for this user
        creator_payouts = Payout.query.filter_by(
            user_id=user.id,
            payout_type='creator'
        ).all()
        print(f"\nFound {len(creator_payouts)} 'creator' payouts for this user.")

if __name__ == '__main__':
    inspect_financials()
