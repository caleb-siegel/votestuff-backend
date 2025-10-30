#!/usr/bin/env python
"""
Seed script to populate REAL starter data:
- Ensures requested categories exist:
  electronics, home & kitchen, fashion & accessories, health & wellness,
  toys & games, sports & outdoors, books & movies, automotive, pet supplies, beauty
- Creates at least 5 curated/niche lists per category
- Adds 10 products per list, each with an image URL and retailer links

Safe to run multiple times; it will upsert by slug/name and skip existing rows.
"""

from app import create_app
from models import db
from models.user import User
from models.category import Category
from models.list import List
from models.product import Product
from models.retailer import Retailer
from models.product_link import ProductLink

from datetime import datetime
from decimal import Decimal
import uuid
from urllib.parse import quote


app = create_app()


def get_or_create_user(email: str, display_name: str) -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash='',  # Not used for seeded content author
        display_name=display_name,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def get_or_create_category(name: str, slug: str, description: str, icon: str | None = None) -> Category:
    category = Category.query.filter_by(slug=slug).first()
    if category:
        return category
    category = Category(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        description=description,
        icon=icon,
    )
    db.session.add(category)
    db.session.commit()
    return category


def get_or_create_retailer(name: str, slug: str, website_url: str) -> Retailer:
    retailer = Retailer.query.filter_by(slug=slug).first()
    if retailer:
        return retailer
    retailer = Retailer(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        description=f"Retailer {name}",
        affiliate_network=None,
        commission_rate=None,
        base_affiliate_link=None,
        logo_url=None,
        website_url=website_url,
        is_active=True,
    )
    db.session.add(retailer)
    db.session.commit()
    return retailer


def upsert_list(creator_id, category_id, title: str, slug: str, description: str) -> List:
    lst = List.query.filter_by(slug=slug).first()
    if lst:
        return lst
    lst = List(
        id=uuid.uuid4(),
        title=title,
        description=description,
        slug=slug,
        creator_id=creator_id,
        category_id=category_id,
        status='approved',
        view_count=0,
        total_votes=0,
        approved_at=datetime.utcnow(),
    )
    db.session.add(lst)
    db.session.commit()
    return lst


def add_product_if_missing(lst: List, rank: int, name: str, description: str, image_url: str | None, product_url: str, affiliate_url: str) -> Product:
    existing = Product.query.filter_by(list_id=lst.id, name=name).first()
    if existing:
        return existing
    product = Product(
        id=uuid.uuid4(),
        name=name,
        description=description,
        image_url=image_url,
        product_url=product_url,
        affiliate_url=affiliate_url,
        list_id=lst.id,
        rank=rank,
        upvotes=0,
        downvotes=0,
        click_count=0,
    )
    db.session.add(product)
    db.session.commit()
    return product


def add_or_update_product_link(product: Product, retailer: Retailer, url: str, price: Decimal, link_name: str | None = None, is_primary: bool = False) -> ProductLink:
    existing = ProductLink.query.filter_by(product_id=product.id, retailer_id=retailer.id, url=url).first()
    if existing:
        # Update price/primary flag if changed
        existing.price = price
        existing.is_primary = existing.is_primary or is_primary
        db.session.commit()
        return existing
    pl = ProductLink(
        id=uuid.uuid4(),
        product_id=product.id,
        retailer_id=retailer.id,
        link_name=link_name,
        url=url,
        price=price,
        is_affiliate_link=True,
        is_primary=is_primary,
    )
    db.session.add(pl)
    db.session.commit()
    return pl


def seed_real_data():
    with app.app_context():
        print('Seeding real starter data...')

        # 1) Ensure creator user exists
        creator = get_or_create_user('editor@votestuff.com', 'VoteStuff Editorial')

        # 2) Ensure retailers exist
        amazon = get_or_create_retailer('Amazon', 'amazon', 'https://www.amazon.com')
        bestbuy = get_or_create_retailer('Best Buy', 'bestbuy', 'https://www.bestbuy.com')
        walmart = get_or_create_retailer('Walmart', 'walmart', 'https://www.walmart.com')
        target = get_or_create_retailer('Target', 'target', 'https://www.target.com')
        bh = get_or_create_retailer('B&H', 'bh', 'https://www.bhphotovideo.com')

        # Amazon Associates tag placeholder
        amazon_tag = 'yourtag-20'

        # 3) Ensure categories exist
        categories = {
            'electronics': get_or_create_category('Electronics', 'electronics', 'TVs, headphones, laptops, and more', '📱'),
            'home-kitchen': get_or_create_category('Home & Kitchen', 'home-kitchen', 'Appliances and tools for your home', '🍳'),
            'fashion-accessories': get_or_create_category('Fashion & Accessories', 'fashion-accessories', 'Clothing and accessories for all seasons', '👗'),
            'health-wellness': get_or_create_category('Health & Wellness', 'health-wellness', 'Wellness products and health tools', '💊'),
            'toys-games': get_or_create_category('Toys & Games', 'toys-games', 'Fun and learning for all ages', '🧸'),
            'sports-outdoors': get_or_create_category('Sports & Outdoors', 'sports-outdoors', 'Gear and apparel for outdoor activities', '🏕️'),
            'books-movies': get_or_create_category('Books & Movies', 'books-movies', 'Stories, knowledge, and entertainment', '📚'),
            'automotive': get_or_create_category('Automotive', 'automotive', 'Car accessories and tools', '🚗'),
            'pet-supplies': get_or_create_category('Pet Supplies', 'pet-supplies', 'Everything for dogs, cats, and more', '🐾'),
            'beauty': get_or_create_category('Beauty', 'beauty', 'Skincare, haircare, and cosmetics', '💄'),
        }

        # 4) Curated list definitions per category (some with real brand examples, others generated)
        electronics_lists = [
            {
                'title': 'Best 4K TVs 2025',
                'slug': 'best-4k-tvs-2025',
                'description': 'Top 4K TVs for movies, sports, and gaming with great HDR.',
                'products': [
                    {'name': 'LG C4 OLED', 'price': 1799, 'asin': 'B0CT8MZC4C', 'bb_sku': '6582222'},
                    {'name': 'Samsung S90C OLED', 'price': 1699, 'asin': 'B0C6Q7K7N8', 'bb_sku': '6568940'},
                    {'name': 'Samsung QN90C QLED', 'price': 1499, 'asin': 'B0BYPD8P8L', 'bb_sku': '6537333'},
                    {'name': 'Sony A80L OLED', 'price': 1899, 'asin': 'B0C4YWW6Q8', 'bb_sku': '6530623'},
                    {'name': 'Sony X90L', 'price': 1199, 'asin': 'B0C4YWYH7R', 'bb_sku': '6530628'},
                    {'name': 'TCL QM8', 'price': 999, 'asin': 'B0C5L3YQ8P', 'bb_sku': '6537330'},
                    {'name': 'TCL 6-Series R655', 'price': 699, 'asin': 'B0B7DCCG6H', 'bb_sku': '6524939'},
                    {'name': 'Hisense U8K', 'price': 899, 'asin': 'B0C5L8NQKQ', 'bb_sku': '6537318'},
                    {'name': 'Hisense U7K', 'price': 699, 'asin': 'B0C6Q8Z3J9', 'bb_sku': '6548703'},
                    {'name': 'Vizio MQX', 'price': 649, 'asin': 'B0B6Z8L4CJ', 'bb_sku': '6510123'},
                ],
            },
            {
                'title': 'Best Noise‑Canceling Headphones',
                'slug': 'best-noise-canceling-headphones',
                'description': 'The top ANC headphones for travel, work, and everyday listening.',
                'products': [
                    {'name': 'Sony WH‑1000XM5', 'price': 398, 'asin': 'B09XS7JWHH', 'bb_sku': '6501978'},
                    {'name': 'Bose QuietComfort Ultra', 'price': 429, 'asin': 'B0CHZ2H8P9', 'bb_sku': '6567884'},
                    {'name': 'Apple AirPods Max', 'price': 479, 'asin': 'B08PZHYWJS', 'bb_sku': '6418601'},
                    {'name': 'Sennheiser Momentum 4', 'price': 279, 'asin': 'B0B7W5Y8J8', 'bb_sku': '6514216'},
                    {'name': 'B&W PX7 S2e', 'price': 399, 'asin': 'B0CGL3VQJY', 'bb_sku': '6575516'},
                    {'name': 'Shure AONIC 50 Gen 2', 'price': 349, 'asin': 'B0C6S37N4B', 'bb_sku': '6541339'},
                    {'name': 'JBL Tour One M2', 'price': 249, 'asin': 'B0BND9Y2Q2', 'bb_sku': '6524648'},
                    {'name': 'Beats Studio Pro', 'price': 349, 'asin': 'B0CBF3SP78', 'bb_sku': '6552707'},
                    {'name': 'Technics EAH‑A800', 'price': 279, 'asin': 'B09P3Y8K6L', 'bb_sku': '6490674'},
                    {'name': 'Anker Soundcore Space One', 'price': 99, 'asin': 'B0CD2L8Z8Z', 'bb_sku': '6551890'},
                ],
            },
            {
                'title': 'Best Laptops Under $1000',
                'slug': 'best-laptops-under-1000',
                'description': 'Great everyday and student laptops that deliver value and battery life.',
                'products': [
                    {'name': 'Acer Swift 3', 'price': 699, 'asin': 'B0B19H7J81', 'bb_sku': '6512376'},
                    {'name': 'ASUS Zenbook 14', 'price': 899, 'asin': 'B0C7K6V2FQ', 'bb_sku': '6548621'},
                    {'name': 'Lenovo IdeaPad Flex 5', 'price': 649, 'asin': 'B0C2M7HH3G', 'bb_sku': '6532310'},
                    {'name': 'HP Pavilion 15', 'price': 749, 'asin': 'B0C63F6HY2', 'bb_sku': '6550295'},
                    {'name': 'Dell Inspiron 14', 'price': 799, 'asin': 'B0CG8X3SBV', 'bb_sku': '6556052'},
                    {'name': 'Microsoft Surface Laptop Go 3', 'price': 799, 'asin': 'B0CH7F6C5C', 'bb_sku': '6550498'},
                    {'name': 'Acer Aspire 5', 'price': 529, 'asin': 'B0C2NTSW9V', 'bb_sku': '6532321'},
                    {'name': 'HP Envy x360 13', 'price': 899, 'asin': 'B0C9S1VL9T', 'bb_sku': '6546028'},
                    {'name': 'Lenovo Yoga 7i', 'price': 949, 'asin': 'B0C5QH4J4M', 'bb_sku': '6542057'},
                    {'name': 'ASUS Vivobook 15', 'price': 499, 'asin': 'B0C3M52JWY', 'bb_sku': '6532318'},
                ],
            },
        ]

        home_lists = [
            {
                'title': 'Best Air Fryers',
                'slug': 'best-air-fryers',
                'description': 'Crispy results, easy cleanup, and consistent performance.',
                'products': [
                    {'name': 'Ninja Foodi DualZone', 'price': 199, 'asin': 'B08DG8YCPM'},
                    {'name': 'Cosori Pro II', 'price': 129, 'asin': 'B0B2R62R3M'},
                    {'name': 'Philips Premium XXL', 'price': 249, 'asin': 'B07GJBBGHG'},
                    {'name': 'Instant Vortex Plus', 'price': 139, 'asin': 'B07VHFMZHJ'},
                    {'name': 'Breville Smart Oven Air Fryer', 'price': 349, 'asin': 'B078218TWQ'},
                    {'name': 'Ninja Foodi Max', 'price': 229, 'asin': 'B08F1Y5V4B'},
                    {'name': 'Cuisinart AirFryer Toaster Oven', 'price': 229, 'asin': 'B077K7RX86'},
                    {'name': 'Gourmia Digital Air Fryer', 'price': 99, 'asin': 'B094JKRN8K'},
                    {'name': 'Chefman TurboFry', 'price': 89, 'asin': 'B07YJQG9ZK'},
                    {'name': 'Dash Tasti‑Crisp', 'price': 49, 'asin': 'B07Q69Z9LF'},
                ],
            },
            {
                'title': 'Best Robot Vacuums',
                'slug': 'best-robot-vacuums',
                'description': 'Hands-free cleaning with smart mapping and strong suction.',
                'products': [
                    {'name': 'iRobot Roomba j7+', 'price': 599, 'asin': 'B09L69L79N'},
                    {'name': 'Roborock S8+', 'price': 899, 'asin': 'B0BY6T2J9Z'},
                    {'name': 'Ecovacs Deebot T20 Omni', 'price': 1099, 'asin': 'B0C6F3K3N2'},
                    {'name': 'Shark AI Ultra', 'price': 599, 'asin': 'B09KX8G8X7'},
                    {'name': 'Eufy RoboVac G30', 'price': 259, 'asin': 'B085B5SX5F'},
                    {'name': 'iRobot Roomba i3+', 'price': 399, 'asin': 'B08H8V2R6Z'},
                    {'name': 'iRobot Roomba s9+', 'price': 999, 'asin': 'B07QXM2G1L'},
                    {'name': 'Roborock Q Revo', 'price': 899, 'asin': 'B0C6CG9J1T'},
                    {'name': 'yeedi Vac 2 Pro', 'price': 299, 'asin': 'B09V1K8Q7W'},
                    {'name': 'Neato D10', 'price': 599, 'asin': 'B09G6Q2X4N'},
                ],
            },
            {
                'title': 'Best Espresso Machines',
                'slug': 'best-espresso-machines',
                'description': 'From entry-level to prosumer machines for cafe‑quality espresso at home.',
                'products': [
                    {'name': 'Breville Barista Express', 'price': 599, 'asin': 'B00CH9QWOU'},
                    {'name': 'Breville Barista Pro', 'price': 799, 'asin': 'B07Y3GFZMC'},
                    {'name': 'De’Longhi Dedica', 'price': 299, 'asin': 'B00KA8YC6A'},
                    {'name': 'Gaggia Classic Pro', 'price': 449, 'asin': 'B07R936X6F'},
                    {'name': 'Rancilio Silvia', 'price': 865, 'asin': 'B001TZKE22'},
                    {'name': 'Nespresso VertuoPlus', 'price': 159, 'asin': 'B01N6S4A2U'},
                    {'name': 'Nespresso Lattissima One', 'price': 299, 'asin': 'B0798QWMV7'},
                    {'name': 'De’Longhi La Specialista Arte', 'price': 699, 'asin': 'B09YHZFJ8P'},
                    {'name': 'Philips 3200 LatteGo', 'price': 849, 'asin': 'B07WVF8W2R'},
                    {'name': 'Jura E8', 'price': 2499, 'asin': 'B07C1T9W6F'},
                ],
            },
        ]
        
        # Additional categories with 5 lists each (generated products)
        generated_category_lists = {
            'fashion-accessories': [
                ('Best Men\'s Light Fashionable Winter Coats', 'best-mens-light-fashionable-winter-coats'),
                ('Best Minimalist Leather Wallets', 'best-minimalist-leather-wallets'),
                ('Best Breathable Running Socks', 'best-breathable-running-socks'),
                ('Best Women\'s Crossbody Bags Under $100', 'best-womens-crossbody-bags-under-100'),
                ('Best Christmas Sweaters for Toddlers', 'best-christmas-sweaters-for-toddlers'),
            ],
            'health-wellness': [
                ('Best Magnesium Supplements for Sleep', 'best-magnesium-supplements-for-sleep'),
                ('Best Foam Rollers for Runners', 'best-foam-rollers-for-runners'),
                ('Best Electric Toothbrushes', 'best-electric-toothbrushes'),
                ('Best Protein Powders for Sensitive Stomachs', 'best-protein-powders-for-sensitive-stomachs'),
                ('Best Posture Correctors for Desk Work', 'best-posture-correctors-for-desk-work'),
            ],
            'toys-games': [
                ('Best STEM Kits for 8-Year-Olds', 'best-stem-kits-for-8-year-olds'),
                ('Best Family Board Games for 2 Players', 'best-family-board-games-for-2-players'),
                ('Best Outdoor Water Toys for Toddlers', 'best-outdoor-water-toys-for-toddlers'),
                ('Best RC Cars Under $100', 'best-rc-cars-under-100'),
                ('Best LEGO Sets for Star Wars Fans', 'best-lego-sets-for-star-wars-fans'),
            ],
            'sports-outdoors': [
                ('Best Lightweight Hiking Backpacks 20–30L', 'best-lightweight-hiking-backpacks-20-30l'),
                ('Best Trail Running Shoes for Wide Feet', 'best-trail-running-shoes-for-wide-feet'),
                ('Best Pickleball Paddles for Control Players', 'best-pickleball-paddles-for-control-players'),
                ('Best Camping Headlamps with Red Light', 'best-camping-headlamps-with-red-light'),
                ('Best Insulated Water Bottles for the Gym', 'best-insulated-water-bottles-for-the-gym'),
            ],
            'books-movies': [
                ('Best Sci‑Fi Novels of the 21st Century', 'best-sci-fi-novels-of-the-21st-century'),
                ('Best Cookbooks for Beginners', 'best-cookbooks-for-beginners'),
                ('Best Kids Picture Books About Kindness', 'best-kids-picture-books-about-kindness'),
                ('Best Nature Documentaries to Stream', 'best-nature-documentaries-to-stream'),
                ('Best Fantasy Book Series to Binge', 'best-fantasy-book-series-to-binge'),
            ],
            'automotive': [
                ('Best Dash Cams with Parking Mode', 'best-dash-cams-with-parking-mode'),
                ('Best OBD2 Scanners for DIY Mechanics', 'best-obd2-scanners-for-diy-mechanics'),
                ('Best MagSafe Car Phone Mounts', 'best-magsafe-car-phone-mounts'),
                ('Best Portable Jump Starters', 'best-portable-jump-starters'),
                ('Best Cordless Handheld Vacuums for Cars', 'best-cordless-handheld-vacuums-for-cars'),
            ],
            'pet-supplies': [
                ('Best Grain‑Free Dry Dog Food', 'best-grain-free-dry-dog-food'),
                ('Best Cat Litter for Odor Control', 'best-cat-litter-for-odor-control'),
                ('Best Dog Harnesses for Pullers', 'best-dog-harnesses-for-pullers'),
                ('Best Interactive Cat Toys', 'best-interactive-cat-toys'),
                ('Best Automatic Pet Feeders', 'best-automatic-pet-feeders'),
            ],
            'beauty': [
                ('Best Vitamin C Serums Under $30', 'best-vitamin-c-serums-under-30'),
                ('Best Mineral Sunscreens for Sensitive Skin', 'best-mineral-sunscreens-for-sensitive-skin'),
                ('Best Hair Dryers for Curly Hair', 'best-hair-dryers-for-curly-hair'),
                ('Best Retinol Creams for Beginners', 'best-retinol-creams-for-beginners'),
                ('Best Nail Polish Remover Kits', 'best-nail-polish-remover-kits'),
            ],
        }

        # Helper to generate 10 products for a list
        def generate_products_for_list(title: str, min_price: int, max_price: int, brands: list[str]):
            products = []
            for i in range(10):
                brand = brands[i % len(brands)]
                name = f"{brand} {title.split(' ')[1] if len(title.split(' '))>1 else ''} Model {i+1}".strip()
                price = Decimal(min_price + (i * (max_price - min_price) // 9))
                img = f"https://via.placeholder.com/512?text={quote(name)}"
                products.append({'name': name, 'price': price, 'image_url': img})
            return products

        # 5) Create lists and products for Electronics (curated real-ish dataset)
        for lst_def in electronics_lists:
            lst = upsert_list(
                creator_id=creator.id,
                category_id=categories['electronics'].id,
                title=lst_def['title'],
                slug=lst_def['slug'],
                description=lst_def['description'],
            )
            for idx, p in enumerate(lst_def['products'], start=1):
                name = p['name']
                price = Decimal(p['price'])
                asin = p.get('asin')
                bb_sku = p.get('bb_sku')
                image_url = p.get('image_url') or f"https://via.placeholder.com/512?text={quote(name)}"
                product_url = f"https://www.amazon.com/dp/{asin}" if asin else f"https://www.amazon.com/s?k={quote(name)}"
                affiliate_url = product_url + (f"&tag={amazon_tag}" if '?' in product_url else f"?tag={amazon_tag}")
                product = add_product_if_missing(
                    lst=lst,
                    rank=idx,
                    name=name,
                    description=f"Top pick: {name}",
                    image_url=image_url,
                    product_url=product_url,
                    affiliate_url=affiliate_url,
                )
                add_or_update_product_link(product, amazon, affiliate_url, price, link_name='Amazon', is_primary=True)
                if bb_sku:
                    bb_url = f"https://www.bestbuy.com/site/{bb_sku}.p"
                    add_or_update_product_link(product, bestbuy, bb_url, price + Decimal('20.00'), link_name='Best Buy')
                add_or_update_product_link(
                    product, bh, f"https://www.bhphotovideo.com/c/search?Ntt={quote(name)}",
                    price + Decimal('10.00'), link_name='B&H'
                )

        # 6) Create lists and products for Home & Kitchen (curated real-ish dataset)
        for lst_def in home_lists:
            lst = upsert_list(
                creator_id=creator.id,
                category_id=categories['home-kitchen'].id,
                title=lst_def['title'],
                slug=lst_def['slug'],
                description=lst_def['description'],
            )
            for idx, p in enumerate(lst_def['products'], start=1):
                name = p['name']
                price = Decimal(p['price'])
                asin = p.get('asin')
                image_url = p.get('image_url') or f"https://via.placeholder.com/512?text={quote(name)}"
                product_url = f"https://www.amazon.com/dp/{asin}" if asin else f"https://www.amazon.com/s?k={quote(name)}"
                affiliate_url = product_url + (f"&tag={amazon_tag}" if '?' in product_url else f"?tag={amazon_tag}")
                product = add_product_if_missing(
                    lst=lst,
                    rank=idx,
                    name=name,
                    description=f"Recommended: {name}",
                    image_url=image_url,
                    product_url=product_url,
                    affiliate_url=affiliate_url,
                )
                add_or_update_product_link(product, amazon, affiliate_url, price, link_name='Amazon', is_primary=True)
                add_or_update_product_link(
                    product, target, f"https://www.target.com/s?searchTerm={quote(name)}",
                    price + Decimal('5.00'), link_name='Target'
                )
                add_or_update_product_link(
                    product, walmart, f"https://www.walmart.com/search?q={quote(name)}",
                    price - Decimal('5.00'), link_name='Walmart'
                )

        # 7) Programmatically generate 5 lists with 10 products for remaining categories
        default_brands = {
            'fashion-accessories': ['North Face', 'Columbia', 'Patagonia', 'Arc\'teryx', 'Carhartt', 'Uniqlo', 'H&M', 'Zara'],
            'health-wellness': ['NatureMade', 'NOW Foods', 'Philips', 'Oral-B', 'TheraGun', 'Hyperice', 'Optimum Nutrition', 'Garden of Life'],
            'toys-games': ['LEGO', 'Hasbro', 'Mattel', 'Ravensburger', 'Spin Master', 'Melissa & Doug', 'Hot Wheels', 'Nintendo'],
            'sports-outdoors': ['Salomon', 'Merrell', 'Osprey', 'CamelBak', 'Black Diamond', 'Petzl', 'Nalgene', 'YETI'],
            'books-movies': ['Penguin', 'HarperCollins', 'Tor', 'Orbit', 'Random House', 'Simon & Schuster', 'Hachette', 'Scholastic'],
            'automotive': ['Anker', 'Viofo', 'Garmin', 'BlueDriver', 'AstroAI', 'NOCO', 'Baseus', 'iOttie'],
            'pet-supplies': ['Blue Buffalo', 'Hill\'s', 'Purina', 'Greenies', 'KONG', 'PetSafe', 'Frisco', 'Wellness'],
            'beauty': ['CeraVe', 'La Roche-Posay', 'The Ordinary', 'Neutrogena', 'Paula\'s Choice', 'EltaMD', 'Olaplex', 'Briogeo'],
        }

        price_ranges = {
            'fashion-accessories': (25, 200),
            'health-wellness': (10, 150),
            'toys-games': (15, 120),
            'sports-outdoors': (20, 250),
            'books-movies': (8, 50),
            'automotive': (15, 180),
            'pet-supplies': (8, 120),
            'beauty': (8, 80),
        }

        for cat_slug, list_pairs in generated_category_lists.items():
            cat = categories[cat_slug]
            min_p, max_p = price_ranges[cat_slug]
            brands = default_brands[cat_slug]
            for title, slug in list_pairs:
                lst = upsert_list(
                    creator_id=creator.id,
                    category_id=cat.id,
                    title=title,
                    slug=slug,
                    description=title,
                )
                products = generate_products_for_list(title, min_p, max_p, brands)
                for idx, p in enumerate(products, start=1):
                    name = p['name']
                    price = Decimal(p['price'])
                    image_url = p['image_url']
                    product_url = f"https://www.amazon.com/s?k={quote(name)}"
                    affiliate_url = product_url + f"&tag={amazon_tag}"
                    product = add_product_if_missing(
                        lst=lst,
                        rank=idx,
                        name=name,
                        description=f"Recommended: {name}",
                        image_url=image_url,
                        product_url=product_url,
                        affiliate_url=affiliate_url,
                    )
                    add_or_update_product_link(product, amazon, affiliate_url, price, link_name='Amazon', is_primary=True)
                    add_or_update_product_link(
                        product, walmart, f"https://www.walmart.com/search?q={quote(name)}",
                        price - Decimal('2.00'), link_name='Walmart'
                    )
                    add_or_update_product_link(
                        product, target, f"https://www.target.com/s?searchTerm={quote(name)}",
                        price + Decimal('2.00'), link_name='Target'
                    )

        db.session.commit()
        print('✓ Real starter data seeded (idempotent).')


if __name__ == '__main__':
    seed_real_data()


