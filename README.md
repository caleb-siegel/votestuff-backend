# VoteStuff Backend API

Flask backend API for VoteStuff.com

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Update `.env` with your Supabase database URL:
```
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.qnknucikjqfinczkaetz.supabase.co:5432/postgres
```

4. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run the development server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Deployment to Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
cd backend
vercel
```

4. Set environment variables in Vercel dashboard or via CLI:
```bash
vercel env add DATABASE_URL
vercel env add SECRET_KEY
```

5. Run database migrations on production:
```bash
vercel exec flask db upgrade
```

## API Endpoints

### Health Check
- `GET /health` - Check API status

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/oauth` - OAuth login

### Lists
- `GET /api/lists` - Get all lists
- `GET /api/lists/<id>` - Get single list
- `POST /api/lists` - Create new list
- `GET /api/lists/trending` - Get trending lists

### Products
- `GET /api/products/<id>` - Get single product
- `POST /api/lists/<list_id>/products` - Add product to list
- `POST /api/products/<id>/click` - Track click

### Voting
- `POST /api/products/<id>/vote` - Vote on product
- `GET /api/products/<id>/vote-status` - Get vote status

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/<id>` - Get single category
- `GET /api/categories/slug/<slug>` - Get category by slug

### Users
- `GET /api/users/<id>` - Get user profile
- `PUT /api/users/<id>/update` - Update user profile

### Wishlist
- `GET /api/users/<id>/wishlist` - Get user wishlist
- `POST /api/users/<id>/wishlist` - Add to wishlist
- `DELETE /api/users/<id>/wishlist/<product_id>` - Remove from wishlist

### Contact
- `POST /api/contact` - Submit contact form

### Search
- `GET /api/search?q=<query>` - Search across lists, products, categories

### Admin (requires admin auth)
- `POST /api/admin/lists/<id>/approve` - Approve list
- `POST /api/admin/lists/<id>/reject` - Reject list
- `GET /api/admin/contact-submissions` - Get contact submissions
- `GET /api/admin/payouts` - Get all payouts

### Analytics (requires auth)
- `GET /api/analytics/clicks` - Get click analytics
- `GET /api/analytics/conversions` - Get conversion analytics

## Database Models

- **User** - User accounts
- **Category** - Product categories
- **List** - Listicles created by users
- **Product** - Products within lists
- **Vote** - User votes on products
- **Wishlist** - User wishlist items
- **AffiliateClick** - Affiliate link click tracking
- **Conversion** - Affiliate conversion tracking
- **Payout** - Payouts to list creators
- **ContactSubmission** - Contact form submissions

## Migrations

To create a new migration:
```bash
flask db migrate -m "Description of changes"
```

To apply migrations:
```bash
flask db upgrade
```

To rollback:
```bash
flask db downgrade
```

