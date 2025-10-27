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
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'])
    
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

