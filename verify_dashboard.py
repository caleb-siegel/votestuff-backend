
from app import create_app
from models import db, User, List
import uuid

app = create_app()

def verify_dashboard():
    with app.app_context():
        # Find a user with lists
        # We'll try to find a user who has lists, or just the first user
        user = User.query.join(List).first()
        
        if not user:
            print("No users with lists found in the database.")
            # Try to find any user
            user = User.query.first()
            if not user:
                print("No users found at all.")
                return

        print(f"Testing dashboard for user: {user.display_name} ({user.id})")
        
        # specific import to test the route function directly if needed, 
        # but better to use the test client
        client = app.test_client()
        
        response = client.get(f'/api/users/{user.id}/dashboard')
        
        if response.status_code == 200:
            data = response.get_json()
            print("\nDashboard Data Retrieved Successfully!")
            print("-" * 30)
            print(f"Total Lists: {data['overview']['total_lists']}")
            print(f"Total Views: {data['overview']['total_views']}")
            print(f"Total Clicks: {data['overview']['total_clicks']}")
            print(f"Total Earnings: ${data['overview']['total_earnings']}")
            print("-" * 30)
            
            # Verify Chart Data
            print("\nVerifying Chart Data:")
            print(f"Performance History Entries: {len(data.get('performance_history', []))}")
            if data.get('performance_history'):
                first_entry = data['performance_history'][0]
                print(f"First Entry Date: {first_entry['date']}")
                print(f"Keys in first entry: {list(first_entry.keys())}")
                
            print(f"Earnings Breakdown Entries: {len(data.get('earnings_breakdown', []))}")
            if data.get('earnings_breakdown'):
                for entry in data['earnings_breakdown']:
                    print(f"  - {entry['name']}: ${entry['value']}")
            
            print("-" * 30)
            
            if data['lists']:
                first_list = data['lists'][0]
                print(f"\nFirst List: {first_list['title']}")
                print(f"Stats: {first_list['view_count']} views, {first_list['click_count']} clicks")
                print(f"Financials: Rev=${first_list.get('revenue', 0)}, Earn=${first_list['earnings']}")
            else:
                print("\nUser has no lists (or none returned).")
                
        else:
            print(f"\nFailed to retrieve dashboard data. Status: {response.status_code}")
            print(f"Error: {response.get_json()}")

if __name__ == '__main__':
    verify_dashboard()
