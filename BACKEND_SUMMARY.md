# VoteStuff Backend - Summary

## Overview

A complete Flask-based REST API backend for VoteStuff.com, designed to handle user authentication, list creation, voting, affiliate tracking, and payouts.

## ✅ What's Been Built

### 1. Database Models (10 tables)

#### Core Models
- **User** - User accounts with authentication, profiles, and financial tracking
- **Category** - Product categories with icons and metadata
- **List** - Listicles created by users with approval workflow
- **Product** - Products within lists with affiliate links

#### Activity Tracking
- **Vote** - User votes on products (supports anonymous users)
- **Wishlist** - User wishlist items

#### Financial & Analytics
- **AffiliateClick** - Tracks affiliate link clicks
- **Conversion** - Tracks affiliate conversions and revenue
- **Payout** - Payout records for list creators

#### Contact
- **ContactSubmission** - Contact form submissions

### 2. API Routes

#### Authentication (`/api/auth/`)
- `POST /auth/register` - Register new users
- `POST /auth/login` - User login
- `POST /auth/oauth` - OAuth login (placeholder)

#### Lists (`/api/lists/`)
- `GET /lists` - Get all lists (with pagination, filtering, sorting)
- `GET /lists/<id>` - Get single list with products
- `POST /lists` - Create new list
- `GET /lists/trending` - Get trending lists

#### Products (`/api/products/`)
- `GET /products/<id>` - Get single product
- `POST /lists/<id>/products` - Add product to list
- `POST /products/<id>/click` - Track affiliate click

#### Voting (`/api/votes/`)
- `POST /products/<id>/vote` - Vote on product (up/down)
- `GET /products/<id>/vote-status` - Get user's vote status

#### Categories (`/api/categories/`)
- `GET /categories` - Get all categories
- `GET /categories/<id>` - Get single category
- `GET /categories/slug/<slug>` - Get category by slug

#### Users (`/api/users/`)
- `GET /users/<id>` - Get user profile with lists
- `PUT /users/<id>/update` - Update user profile

#### Wishlist (`/api/users/<id>/wishlist/`)
- `GET /wishlist` - Get user's wishlist
- `POST /wishlist` - Add product to wishlist
- `DELETE /wishlist/<product_id>` - Remove from wishlist

#### Contact (`/api/contact/`)
- `POST /contact` - Submit contact form

#### Admin (`/api/admin/`)
- `POST /admin/lists/<id>/approve` - Approve list
- `POST /admin/lists/<id>/reject` - Reject list
- `GET /admin/contact-submissions` - Get all submissions
- `GET /admin/payouts` - Get all payouts

#### Analytics (`/api/analytics/`)
- `GET /analytics/clicks` - Click analytics
- `GET /analytics/conversions` - Conversion analytics

#### Search (`/api/search/`)
- `GET /search?q=<query>` - Search across lists, products, categories

### 3. Key Features

#### Dynamic Product Ranking
- Automatically ranks products based on:
  1. Net score (upvotes - downvotes)
  2. Upvote percentage (tie-breaker)
- Updates in real-time when votes are cast

#### Flexible Voting System
- Supports both authenticated and anonymous users
- Users can change or cancel their votes
- Prevents duplicate votes per user/product

#### Affiliate Tracking
- Tracks clicks with user, session, and analytics data
- Records conversions with revenue and commission data
- Links clicks to conversions for attribution

#### Payout System
- Tracks revenue per list creator
- Supports multiple payment methods
- Status tracking: pending, processing, paid, failed

#### Admin Workflow
- Lists require approval before publication
- Admin can approve, reject, or edit lists
- Admin notes for rejected lists

### 4. Configuration

#### Environment Setup
- `.env` file for local development
- `config.py` with development/production configs
- Support for multiple database environments

#### Deployment
- `vercel.json` configured for serverless deployment
- Flask-Migrate for database versioning
- CORS configured for frontend integration

## 📋 Database Schema

See `DATABASE_SCHEMA.md` for complete schema documentation.

## 🚀 Getting Started

### 1. Setup
```bash
cd backend
./setup.sh
```

### 2. Configure
Edit `.env` with your Supabase credentials:
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.qnknucikjqfinczkaetz.supabase.co:5432/postgres
```

### 3. Run
```bash
source venv/bin/activate
python app.py
```

### 4. Test
```bash
curl http://localhost:5000/health
```

## 📝 Next Steps

### Required
1. **Add Authentication Middleware** - Protect routes with JWT tokens
2. **Complete OAuth Integration** - Google and Apple sign-in
3. **Add Input Validation** - Use Flask-WTF or Marshmallow
4. **Add Error Handling** - Global exception handlers
5. **Add Logging** - Request/error logging

### Recommended
1. **Add Caching** - Redis for frequently accessed data
2. **Add Rate Limiting** - Prevent abuse
3. **Add API Documentation** - Swagger/OpenAPI
4. **Add Unit Tests** - pytest for all endpoints
5. **Add CI/CD** - Automated testing and deployment

### Phase 2 Features
1. **WebSocket Support** - Real-time vote updates
2. **Email Notifications** - Send emails for payouts, approvals
3. **Advanced Search** - Full-text search with Postgres
4. **Analytics Dashboard** - Admin analytics UI
5. **Cashback Page** - User cashback tracking

## 📦 Dependencies

- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM
- **Flask-Migrate** - Database migrations
- **Flask-CORS** - CORS support
- **psycopg2-binary** - PostgreSQL driver
- **Werkzeug** - Password hashing utilities

## 🔧 CLI Commands

```bash
# Initialize database
flask init-db

# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Seed categories
flask seed-categories

# Seed admin user
flask seed-admin
```

## 🌐 Deployment

### Vercel

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Deploy:**
```bash
cd backend
vercel
```

3. **Set environment variables:**
```bash
vercel env add DATABASE_URL
vercel env add SECRET_KEY
```

4. **Run migrations:**
```bash
vercel exec flask db upgrade
```

## 📊 API Response Format

### Success Response
```json
{
  "data": {...},
  "message": "Success message"
}
```

### Error Response
```json
{
  "error": "Error message",
  "code": 400
}
```

## 🔒 Security Considerations

1. **Authentication:** Currently basic; needs JWT implementation
2. **Authorization:** Admin checks need to be added to routes
3. **Rate Limiting:** Not implemented yet
4. **Input Validation:** Should add schema validation
5. **SQL Injection:** Protected by SQLAlchemy ORM
6. **XSS:** Should sanitize user input

## 📞 Support

For questions or issues, refer to:
- `README.md` - General documentation
- `INSTALLATION.md` - Setup instructions
- `DATABASE_SCHEMA.md` - Database structure

