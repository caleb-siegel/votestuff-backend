# VoteStuff Backend - Installation Guide

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database (Supabase)
- pip (Python package manager)

### Installation Steps

1. **Navigate to the backend directory:**
```bash
cd backend
```

2. **Run the setup script:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create a virtual environment
- Install all required dependencies
- Create a `.env` file from `env.example`
- Initialize the database
- Create initial migration
- Seed categories and admin user

3. **Update your `.env` file with your Supabase credentials:**
```bash
# Edit .env and update the DATABASE_URL
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.qnknucikjqfinczkaetz.supabase.co:5432/postgres
```

4. **Start the development server:**
```bash
source venv/bin/activate  # Activate virtual environment
python app.py
```

The API will be available at `http://localhost:5000`

## Manual Installation

If you prefer to install manually:

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your database URL
```

4. **Initialize the database:**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Seed initial data:**
```bash
flask seed-categories
flask seed-admin
```

6. **Run the application:**
```bash
python app.py
```

## Database Migrations

### Create a new migration
```bash
flask db migrate -m "Description of changes"
```

### Apply migrations
```bash
flask db upgrade
```

### Rollback last migration
```bash
flask db downgrade
```

## Testing the API

### Health Check
```bash
curl http://localhost:5000/health
```

### Test Auth Route
```bash
curl http://localhost:5000/api/auth/test
```

### Register a User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "display_name": "Test User"
  }'
```

### Get Categories
```bash
curl http://localhost:5000/api/categories
```

## Default Admin Credentials

After seeding, you can login with:
- **Email:** admin@votestuff.com
- **Password:** admin123

⚠️ **Important:** Change these credentials in production!

## Environment Variables

The following environment variables are available:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | Flask secret key | dev-secret-key |
| `JWT_SECRET_KEY` | JWT token secret | jwt-secret-key |
| `FLASK_ENV` | Flask environment | development |
| `FLASK_DEBUG` | Enable debug mode | 1 |
| `CORS_ORIGINS` | Allowed CORS origins | * |
| `PARTNERIZE_API_KEY` | Partnerize API key | - |
| `AMAZON_ASSOCIATES_TAG` | Amazon Associates tag | - |

## Troubleshooting

### Import Errors
If you encounter import errors, make sure you're running commands from the `backend` directory and that the virtual environment is activated.

### Database Connection Errors
- Verify your Supabase credentials in `.env`
- Check that your IP is whitelisted in Supabase settings
- Ensure the database exists and is accessible

### Migration Errors
If migrations fail:
```bash
# Drop all tables and start fresh
flask db downgrade -1
flask db migrate -m "Fresh start"
flask db upgrade
```

### Port Already in Use
If port 5000 is already in use:
```bash
# Change the port in app.py
app.run(debug=True, port=5001)
```

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── manage.py             # CLI commands
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel deployment config
├── env.example           # Environment variables template
├── setup.sh              # Setup script
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── category.py
│   ├── list.py
│   ├── product.py
│   ├── vote.py
│   ├── wishlist.py
│   ├── affiliate_click.py
│   ├── conversion.py
│   ├── payout.py
│   └── contact_submission.py
├── routes/               # API routes
│   ├── __init__.py
│   ├── auth.py
│   ├── lists.py
│   ├── products.py
│   ├── votes.py
│   ├── categories.py
│   ├── users.py
│   ├── wishlist.py
│   ├── contact.py
│   ├── admin.py
│   ├── analytics.py
│   └── search.py
└── migrations/           # Database migrations (created after init)
```

## Next Steps

1. **Connect Frontend:** Update your frontend to point to the backend API
2. **Add Authentication:** Implement JWT tokens for secure API access
3. **Deploy to Vercel:** Use the provided `vercel.json` for deployment
4. **Set Environment Variables:** Configure production environment variables in Vercel

