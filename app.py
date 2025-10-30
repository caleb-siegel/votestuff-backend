"""
VoteStuff Backend API
Flask application for VoteStuff.com
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from config import Config
from models import db
from routes import api_bp

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    # Enable CORS for frontend with proper configuration
    # IMPORTANT: Cannot use origins='*' with supports_credentials=True (browser security restriction)
    # So we explicitly list development origins when credentials are enabled
    cors_origins = app.config.get('CORS_ORIGINS')
    if not cors_origins:
        # Default development origins - must be explicit list when using credentials
        cors_origins = [
            'http://localhost:3000',
            'http://localhost:5173',
            'http://localhost:8080',
            'http://localhost:8081',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:8080',
            'http://127.0.0.1:8081',
        ]
    
    CORS(app,
         origins=cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'ok', 'message': 'VoteStuff API is running'})
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

