# VoteStuff Database Schema

## Overview
This document describes the database schema for VoteStuff.com based on the PRD requirements.

## Tables

### 1. users
Stores user accounts and authentication information.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `email` (String, unique) - User email
- `password_hash` (String, nullable) - Hashed password (null for OAuth users)
- `display_name` (String) - User display name
- `profile_picture` (String, nullable) - Profile picture URL
- `bio` (Text, nullable) - User biography
- `is_admin` (Boolean) - Admin flag
- `is_active` (Boolean) - Account active status
- `oauth_provider` (String, nullable) - OAuth provider (google, apple, etc.)
- `oauth_id` (String, nullable) - OAuth provider ID
- `cashback_balance` (Numeric) - Total cashback balance
- `total_payout` (Numeric) - Total payouts received
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

**Relationships:**
- Has many: lists, votes, wishlist_items, payouts

---

### 2. categories
Stores product categories.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `name` (String, unique) - Category name
- `slug` (String, unique) - URL-friendly category name
- `description` (Text, nullable) - Category description
- `icon` (String, nullable) - Icon name/emoji
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

**Relationships:**
- Has many: lists

---

### 3. lists
Stores listicles created by users.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `title` (String) - List title
- `description` (Text, nullable) - List description
- `slug` (String, unique) - URL-friendly list name
- `creator_id` (UUID, FK) - Foreign key to users
- `category_id` (UUID, FK, nullable) - Foreign key to categories
- `status` (String, indexed) - Status: pending, approved, rejected
- `admin_notes` (Text, nullable) - Admin notes for rejected lists
- `view_count` (Integer) - Total views
- `total_votes` (Integer) - Total votes across all products
- `created_at` (DateTime, indexed) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `approved_at` (DateTime, nullable) - Approval timestamp

**Relationships:**
- Belongs to: creator (user), category
- Has many: products, votes, affiliate_clicks, conversions, payouts

---

### 4. products
Stores products within lists.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `name` (String) - Product name
- `description` (Text, nullable) - Product description
- `image_url` (String, nullable) - Product image URL
- `affiliate_url` (String) - Primary affiliate URL
- `product_url` (String, nullable) - Original product page URL
- `additional_links` (Text, nullable) - JSON string for multiple affiliate sources
- `list_id` (UUID, FK) - Foreign key to lists
- `upvotes` (Integer) - Total upvotes
- `downvotes` (Integer) - Total downvotes
- `rank` (Integer) - Current rank position
- `click_count` (Integer) - Total click count
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

**Computed Properties:**
- `net_score` = upvotes - downvotes
- `upvote_percentage` = (upvotes / (upvotes + downvotes)) * 100

**Relationships:**
- Belongs to: list
- Has many: votes, wishlist_items, affiliate_clicks, conversions

---

### 5. votes
Stores user votes on products.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `product_id` (UUID, FK) - Foreign key to products
- `list_id` (UUID, FK) - Foreign key to lists
- `user_id` (UUID, FK, nullable) - Foreign key to users (null for guests)
- `vote_type` (String) - 'up' or 'down'
- `session_id` (String, nullable) - Session ID for anonymous users
- `ip_address` (String, nullable) - IP address for tracking
- `created_at` (DateTime, indexed) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

**Constraints:**
- Unique constraint on (product_id, user_id) to prevent duplicate votes

**Relationships:**
- Belongs to: user (optional), product, list

---

### 6. wishlist
Stores user wishlist items.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `user_id` (UUID, FK) - Foreign key to users
- `product_id` (UUID, FK) - Foreign key to products
- `created_at` (DateTime, indexed) - Creation timestamp

**Constraints:**
- Unique constraint on (user_id, product_id) to prevent duplicates

**Relationships:**
- Belongs to: user, product

---

### 7. affiliate_clicks
Tracks affiliate link clicks for analytics.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `list_id` (UUID, FK) - Foreign key to lists
- `product_id` (UUID, FK) - Foreign key to products
- `user_id` (UUID, FK, nullable) - Foreign key to users
- `url` (String) - Clicked URL
- `session_id` (String, nullable) - Session ID
- `ip_address` (String, nullable) - IP address
- `user_agent` (String, nullable) - User agent string
- `referrer` (String, nullable) - HTTP referrer
- `has_converted` (Boolean) - Conversion flag
- `created_at` (DateTime, indexed) - Click timestamp
- `converted_at` (DateTime, nullable) - Conversion timestamp

**Relationships:**
- Belongs to: list, product, user (optional)
- Has one: conversion

---

### 8. conversions
Tracks affiliate conversions and revenue.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `click_id` (UUID, FK, nullable) - Foreign key to affiliate_clicks
- `list_id` (UUID, FK) - Foreign key to lists
- `product_id` (UUID, FK) - Foreign key to products
- `revenue` (Numeric) - Total revenue
- `commission` (Numeric) - Commission amount
- `commission_rate` (Numeric) - Commission percentage
- `currency` (String) - Currency code (default: USD)
- `network` (String, nullable) - Affiliate network (amazon, impact, partnerize)
- `external_id` (String, nullable) - External conversion ID
- `created_at` (DateTime, indexed) - Creation timestamp
- `converted_at` (DateTime) - Conversion timestamp

**Relationships:**
- Belongs to: click (optional), list, product
- Has one: payout

---

### 9. payouts
Tracks payouts to list creators.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `user_id` (UUID, FK) - Foreign key to users (creator)
- `list_id` (UUID, FK) - Foreign key to lists
- `conversion_id` (UUID, FK, nullable) - Foreign key to conversions
- `amount` (Numeric) - Payout amount
- `status` (String, indexed) - Status: pending, processing, paid, failed
- `currency` (String) - Currency code (default: USD)
- `payment_method` (String, nullable) - Payment method (paypal, stripe, etc.)
- `payment_reference` (String, nullable) - Payment reference ID
- `admin_notes` (Text, nullable) - Admin notes
- `created_at` (DateTime, indexed) - Creation timestamp
- `paid_at` (DateTime, nullable) - Payment timestamp

**Relationships:**
- Belongs to: user (creator), list, conversion (optional)

---

### 10. contact_submissions
Stores contact form submissions.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `name` (String) - Submitter name
- `email` (String) - Submitter email
- `subject` (String, nullable) - Message subject
- `message` (Text) - Message content
- `status` (String, indexed) - Status: unread, read, replied
- `admin_notes` (Text, nullable) - Admin notes
- `created_at` (DateTime, indexed) - Submission timestamp

---

## Vote Ranking Logic

Products are ranked within lists using the following algorithm:

1. **Primary Sort:** Net Score (descending)
   - Net Score = Upvotes - Downvotes

2. **Tie Breaker:** Upvote Percentage (descending)
   - Upvote Percentage = (Upvotes / Total Votes) × 100

3. **Secondary Tie Breaker:** Most Recent Upvote (if implemented)

The ranking is recalculated whenever a vote is cast or changed.

---

## API Reference

See `README.md` for full API endpoint documentation.

---

## Migration Commands

```bash
# Initialize Flask-Migrate
flask db init

# Create a new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

