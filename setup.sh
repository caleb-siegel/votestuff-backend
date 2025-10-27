#!/bin/bash
# Setup script for VoteStuff backend

echo "🚀 Setting up VoteStuff Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "⚠️  Please update .env with your database credentials!"
fi

# Initialize database
echo "🗄️  Initializing database..."
flask db init

# Create initial migration
echo "📊 Creating initial migration..."
flask db migrate -m "Initial migration"

# Apply migration
echo "✨ Applying migration..."
flask db upgrade

# Seed categories and admin user
echo "🌱 Seeding database..."
flask seed-categories
flask seed-admin

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "The API will be available at http://localhost:5000"

