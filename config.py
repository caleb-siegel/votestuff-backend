"""
Configuration settings for VoteStuff Backend
"""

import os
from urllib.parse import urlparse, parse_qs

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    # Use environment variable or default to local PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:yourpassword@localhost:5432/votestuff'
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # JWT settings (for future authentication)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Affiliate settings
    AFFILIATE_PARTNERIZE = os.environ.get('PARTNERIZE_API_KEY')
    AFFILIATE_AMAZON = os.environ.get('AMAZON_ASSOCIATES_TAG')
    
    # Cashback and payout percentages (as float, e.g., 50.0 = 50%)
    CASHBACK_PERCENTAGE = float(os.environ.get('CASHBACK_PERCENTAGE', '50.0'))  # % of commission to user who clicked
    CREATOR_PAYOUT_PERCENTAGE = float(os.environ.get('CREATOR_PAYOUT_PERCENTAGE', '30.0'))  # % of commission to list creator
    # Remaining percentage stays with platform
    
    # CORS settings
    # In development, allow common localhost ports; in production, use env var
    # This will be loaded by app.py and used for CORS configuration
    cors_origins_env = os.environ.get('CORS_ORIGINS')
    if cors_origins_env:
        CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',')]
    else:
        # Default to allowing common development origins
        CORS_ORIGINS = [
            'http://localhost:3000',
            'http://localhost:5173',
            'http://localhost:8080',
            'http://localhost:8081',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:8080',
            'http://127.0.0.1:8081',
        ]
    
    # Frontend URL for redirects
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:5173'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

