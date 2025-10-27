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
    """Seed initial categories"""
    from models.category import Category
    from datetime import datetime
    import uuid
    
    categories = [
        {'name': 'Electronics', 'slug': 'electronics', 'icon': '📱'},
        {'name': 'Home & Kitchen', 'slug': 'home-kitchen', 'icon': '🍳'},
        {'name': 'Fashion', 'slug': 'fashion', 'icon': '👕'},
        {'name': 'Beauty', 'slug': 'beauty', 'icon': '💄'},
        {'name': 'Health', 'slug': 'health', 'icon': '💊'},
        {'name': 'Toys', 'slug': 'toys', 'icon': '🧸'},
        {'name': 'Sports', 'slug': 'sports', 'icon': '⚽'},
        {'name': 'Books', 'slug': 'books', 'icon': '📚'},
        {'name': 'Automotive', 'slug': 'automotive', 'icon': '🚗'},
        {'name': 'Pets', 'slug': 'pets', 'icon': '🐾'}
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

if __name__ == '__main__':
    app.cli.run()

