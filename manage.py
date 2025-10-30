#!/usr/bin/env python
"""
Management script for VoteStuff backend
"""

import os
from app import create_app
from models import db
import click
from flask.cli import with_appcontext

# Create app instance
app = create_app()

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    click.echo('Database initialized!')

@app.cli.command()
def seed_categories():
    """Seed initial categories (canonical set)."""
    from models.category import Category
    import uuid
    
    categories = [
        {'name': 'Electronics', 'slug': 'electronics', 'icon': '📱'},
        {'name': 'Home & Kitchen', 'slug': 'home-kitchen', 'icon': '🍳'},
        {'name': 'Fashion & Accessories', 'slug': 'fashion-accessories', 'icon': '👗'},
        {'name': 'Health & Wellness', 'slug': 'health-wellness', 'icon': '💊'},
        {'name': 'Toys & Games', 'slug': 'toys-games', 'icon': '🧸'},
        {'name': 'Sports & Outdoors', 'slug': 'sports-outdoors', 'icon': '⚽'},
        {'name': 'Books & Movies', 'slug': 'books-movies', 'icon': '📚'},
        {'name': 'Automotive', 'slug': 'automotive', 'icon': '🚗'},
        {'name': 'Pet Supplies', 'slug': 'pet-supplies', 'icon': '🐾'},
        {'name': 'Beauty', 'slug': 'beauty', 'icon': '💄'},
    ]
    
    for cat_data in categories:
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if not existing:
            category = Category(
                id=uuid.uuid4(),
                name=cat_data['name'],
                slug=cat_data['slug'],
                icon=cat_data['icon']
            )
            db.session.add(category)
            click.echo(f'Added category: {category.name}')
        else:
            # Optionally normalize names/icons on existing
            updated = False
            if existing.name != cat_data['name']:
                existing.name = cat_data['name']
                updated = True
            if existing.icon != cat_data['icon']:
                existing.icon = cat_data['icon']
                updated = True
            if updated:
                click.echo(f'Updated category: {existing.slug}')
    
    db.session.commit()
    click.echo('Categories seeded!')

@app.cli.command()
def seed_admin():
    """Seed admin user"""
    from models.user import User
    from werkzeug.security import generate_password_hash
    import uuid
    
    # Check if admin exists
    admin = User.query.filter_by(email='admin@votestuff.com').first()
    if admin:
        click.echo('Admin user already exists!')
        return
    
    admin = User(
        id=uuid.uuid4(),
        email='admin@votestuff.com',
        password_hash=generate_password_hash('admin123'),
        display_name='Admin',
        is_admin=True,
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    click.echo('Admin user created!')
    click.echo('Email: admin@votestuff.com')
    click.echo('Password: admin123')

@app.cli.command()
def seed_test_data():
    """Seed test/fake data for development"""
    from werkzeug.security import generate_password_hash
    from models.user import User
    from models.category import Category
    from models.list import List
    from models.product import Product
    from models.retailer import Retailer
    from models.product_link import ProductLink
    from models.vote import Vote
    from models.affiliate_click import AffiliateClick
    import uuid
    from datetime import datetime, timedelta
    
    click.echo('Seeding test data...')
    
    # 1. Create test users
    test_users = []
    for i in range(3):
        user = User(
            id=uuid.uuid4(),
            email=f'testuser{i+1}@test.com',
            password_hash=generate_password_hash('test123'),
            display_name=f'Test User {i+1}',
            bio=f'This is test user number {i+1} - fake data for development',
            is_active=True,
            cashback_balance=0.00 + i * 5.50,
            total_payout=0.00
        )
        db.session.add(user)
        test_users.append(user)
    click.echo('✓ Created 3 test users')
    
    # 2. Create test categories
    test_categories = []
    for cat_name, slug, icon in [
        ('TEST Electronics', 'test-electronics', '📱'),
        ('TEST Home & Kitchen', 'test-home-kitchen', '🍳'),
        ('TEST Tech Gadgets', 'test-tech-gadgets', '💻')
    ]:
        category = Category(
            id=uuid.uuid4(),
            name=cat_name,
            slug=slug,
            description=f'Test category: {cat_name} - Fake data for development',
            icon=icon
        )
        db.session.add(category)
        test_categories.append(category)
    click.echo('✓ Created 3 test categories')
    
    # 3. Create test retailers
    test_retailers = []
    for retail_info in [
        {'name': 'TEST Amazon', 'slug': 'test-amazon', 'network': 'Amazon Associates', 'rate': 4.50},
        {'name': 'TEST Best Buy', 'slug': 'test-bestbuy', 'network': 'Impact Radius', 'rate': 3.25},
        {'name': 'TEST Target', 'slug': 'test-target', 'network': 'CJ Affiliate', 'rate': 2.75}
    ]:
        retailer = Retailer(
            id=uuid.uuid4(),
            name=retail_info['name'],
            slug=retail_info['slug'],
            description=f"Test retailer: {retail_info['name']} - fake data",
            affiliate_network=retail_info['network'],
            commission_rate=retail_info['rate'],
            base_affiliate_link=f"https://test.{retail_info['slug']}.com/tag/test-",
            logo_url=f"https://test.com/logos/{retail_info['slug']}.png",
            website_url=f"https://test.{retail_info['slug']}.com",
            is_active=True
        )
        db.session.add(retailer)
        test_retailers.append(retailer)
    click.echo('✓ Created 3 test retailers')
    
    # 4. Create test lists
    test_lists = []
    list_titles = [
        ('TEST Best Wireless Earbuds 2024', 'test-best-wireless-earbuds-2024'),
        ('TEST Top Kitchen Appliances', 'test-top-kitchen-appliances'),
        ('TEST Best Laptops Under $1000', 'test-best-laptops-under-1000')
    ]
    
    for idx, (title, slug) in enumerate(list_titles):
        list_item = List(
            id=uuid.uuid4(),
            title=title,
            description=f'This is a TEST list: {title} - Contains fake data for development purposes only',
            slug=slug,
            creator_id=test_users[0].id,
            category_id=test_categories[idx].id,
            status='approved',
            view_count=100 + idx * 50,
            total_votes=20 + idx * 10,
            approved_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.session.add(list_item)
        test_lists.append(list_item)
    click.echo('✓ Created 3 test lists')
    
    # 5. Create test products (2-3 per list)
    test_products = []
    product_data = [
        # List 1: Earbuds
        ('TEST Sony WH-1000XM4', 'Top test wireless earbuds with noise cancellation', 'https://test.com/sony.png'),
        ('TEST Apple AirPods Pro', 'Premium test wireless earbuds with transparency mode', 'https://test.com/airpods.png'),
        # List 2: Kitchen
        ('TEST Instant Pot Duo', 'Test 7-in-1 pressure cooker for home cooking', 'https://test.com/instantpot.png'),
        ('TEST KitchenAid Mixer', 'Stand mixer perfect for test baking and cooking', 'https://test.com/mixer.png'),
        # List 3: Laptops
        ('TEST Dell XPS 13', 'Compact test laptop with great performance', 'https://test.com/xps.png'),
    ]
    
    product_idx = 0
    for list_item in test_lists:
        products_per_list = 2 if product_idx >= 4 else 2
        for _ in range(products_per_list):
            if product_idx < len(product_data):
                name, desc, img = product_data[product_idx]
                product = Product(
                    id=uuid.uuid4(),
                    name=name,
                    description=desc,
                    image_url=img,
                    affiliate_url=f'https://test.com/product/{product_idx+1}',
                    product_url=f'https://test.com/original/{product_idx+1}',
                    list_id=list_item.id,
                    upvotes=5 + product_idx * 2,
                    downvotes=1 + product_idx,
                    rank=product_idx % 2 + 1,
                    click_count=10 + product_idx * 5,
                    created_at=datetime.utcnow() - timedelta(days=4)
                )
                db.session.add(product)
                test_products.append(product)
                product_idx += 1
    click.echo(f'✓ Created {len(test_products)} test products')
    
    # 6. Create test product links (2-3 per product)
    test_product_links = []
    for product in test_products:
        num_links = min(3, len(test_retailers))
        for retailer_idx, retailer in enumerate(test_retailers[:num_links]):
            is_primary = retailer_idx == 0
            product_link = ProductLink(
                id=uuid.uuid4(),
                product_id=product.id,
                retailer_id=retailer.id,
                link_name=f'Test Link from {retailer.name}',
                url=f'https://test-affiliate-url.com/product/{product.name}',
                is_affiliate_link=True,
                is_primary=is_primary,
                click_count=10,
                created_at=datetime.utcnow() - timedelta(days=3)
            )
            db.session.add(product_link)
            test_product_links.append(product_link)
    click.echo('✓ Created test product links')
    
    # 7. Create test votes
    vote_idx = 0
    for product in test_products:
        for user in test_users[:2]:  # 2 users per product
            vote_type = 'up' if vote_idx % 2 == 0 else 'down'
            vote = Vote(
                id=uuid.uuid4(),
                product_id=product.id,
                list_id=product.list_id,
                user_id=user.id,
                vote_type=vote_type,
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            db.session.add(vote)
            vote_idx += 1
    click.echo('✓ Created test votes')
    
    # 8. Create test affiliate clicks
    for i, product in enumerate(test_products):
        # Pick up to 2 product links for this product
        product_links_for_product = [pl for pl in test_product_links if pl.product_id == product.id]
        for click_idx in range(min(3, len(product_links_for_product) + 1)):
            product_link = product_links_for_product[click_idx] if click_idx < len(product_links_for_product) else None
            click_event = AffiliateClick(
                id=uuid.uuid4(),
                list_id=product.list_id,
                product_id=product.id,
                product_link_id=product_link.id if product_link else None,
                user_id=test_users[(click_idx) % len(test_users)].id if click_idx % 2 == 0 else None,
                url=f'https://test-click-{i}-{click_idx}.com',
                session_id=f'test-session-{i}-{click_idx}',
                ip_address=f'192.168.1.{100+i*3+click_idx}',
                user_agent='Mozilla/5.0 (Test Browser)',
                has_converted=False,
                created_at=datetime.utcnow() - timedelta(hours=5-click_idx)
            )
            db.session.add(click_event)
    click.echo('✓ Created test affiliate clicks')
    
    try:
        db.session.commit()
        click.echo('\n✓ Test data seeded successfully!')
        click.echo('\nTest users (password: test123):')
        for user in test_users:
            click.echo(f'  - {user.email} ({user.display_name})')
    except Exception as e:
        db.session.rollback()
        click.echo(f'\n✗ Error seeding test data: {str(e)}')
        raise

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        with app.app_context():
            # Run the command function directly
            if command == 'seed_categories':
                seed_categories()
            elif command == 'seed_admin':
                seed_admin()
            elif command == 'seed_test_data':
                seed_test_data()
            elif command == 'init_db':
                init_db()
            else:
                print(f"Unknown command: {command}")
                print("Available commands: seed_categories, seed_admin, seed_test_data, init_db")
    else:
        print("Usage: python manage.py <command>")
        print("Available commands: seed_categories, seed_admin, seed_test_data, init_db")

