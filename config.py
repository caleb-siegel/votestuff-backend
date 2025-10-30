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
    
    # CORS settings
    # In development, allow common localhost ports; in production, use env var
    cors_origins = os.environ.get('CORS_ORIGINS')
    if cors_origins:
        CORS_ORIGINS = cors_origins.split(',')
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

