#!/usr/bin/env python
"""
Seed script to populate subcategories with proper parent_id relationships.
This script will:
1. Update all existing categories to have parent_id = NULL (top-level)
2. Add all new subcategories from the user's list with proper parent_id relationships
"""

from app import create_app
from models import db
from models.category import Category
import uuid
import re

app = create_app()


def slugify(name):
    """Convert category name to slug"""
    return re.sub(r'[^\w\s-]', '', name.lower()).strip().replace(' ', '-')


def get_or_create_category(name, slug, parent_id=None, description=None, icon=None):
    """Get or create a category"""
    # First try to find by slug
    category = Category.query.filter_by(slug=slug).first()
    if not category:
        # Try to find by name (for cases where slug might differ)
        category = Category.query.filter_by(name=name).first()
    
    if category:
        # Update fields if they're different
        updated = False
        if category.name != name:
            category.name = name
            updated = True
        if category.slug != slug:
            category.slug = slug
            updated = True
        if category.parent_id != parent_id:
            category.parent_id = parent_id
            updated = True
        if description and category.description != description:
            category.description = description
            updated = True
        if icon and category.icon != icon:
            category.icon = icon
            updated = True
        if updated:
            db.session.commit()
        return category
    
    category = Category(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        parent_id=parent_id,
        description=description,
        icon=icon
    )
    db.session.add(category)
    db.session.commit()
    return category


def seed_subcategories():
    """Seed all subcategories"""
    with app.app_context():
        print('Seeding subcategories...')
        
        # Note: We don't need to reset all categories to NULL first because
        # get_or_create_category will update parent_id correctly based on the seed data
        
        # 2. Define all categories with their hierarchy
        # Format: (name, parent_name, description, icon)
        categories_data = [
            # Top-level categories (parent_name = None)
            ('Electronics', None, 'Electronics and technology products', '📱'),
            ('Home & Kitchen', None, 'Home and kitchen products', '🍳'),
            ('Fashion & Accessories', None, 'Fashion and accessories', '👗'),
            ('Beauty & Personal Care', None, 'Beauty and personal care products', '💄'),
            ('Health & Wellness', None, 'Health and wellness products', '💊'),
            ('Toys & Games', None, 'Toys and games', '🧸'),
            ('Sports & Outdoors', None, 'Sports and outdoor products', '⚽'),
            ('Books & Movies', None, 'Books and movies', '📚'),
            ('Automotive', None, 'Automotive products', '🚗'),
            ('Pet Supplies', None, 'Pet supplies', '🐾'),
            
            # Electronics subcategories
            ('Computers & Laptops', 'Electronics', 'Desktops, laptops, tablets, accessories', '💻'),
            ('Smartphones & Accessories', 'Electronics', 'Smartphones, cases, chargers, headphones', '📱'),
            ('Gaming', 'Electronics', 'Consoles, games, accessories', '🎮'),
            ('Audio & Video', 'Electronics', 'TVs, speakers, headphones, home theater systems', '📺'),
            ('Cameras & Photography', 'Electronics', 'Digital cameras, lenses, accessories', '📷'),
            
            # Smartphones & Accessories subcategories
            ('Smartphones', 'Smartphones & Accessories', 'Smartphones and mobile phones', '📱'),
            ('Phone Cases', 'Smartphones & Accessories', 'Phone cases and protectors', '📱'),
            ('Chargers', 'Smartphones & Accessories', 'Chargers and charging accessories', '🔌'),
            ('Headphones', 'Smartphones & Accessories', 'Headphones and earbuds', '🎧'),
            
            # Gaming subcategories
            ('Gaming Consoles', 'Gaming', 'Gaming consoles and systems', '🎮'),
            ('Video Games', 'Gaming', 'Video games for consoles and PC', '🎮'),
            ('Gaming Accessories', 'Gaming', 'Controllers, headsets, and gaming accessories', '🎮'),
            
            # Audio & Video subcategories
            ('TVs', 'Audio & Video', 'Televisions and smart TVs', '📺'),
            ('Speakers', 'Audio & Video', 'Speakers and sound systems', '🔊'),
            ('Headphones', 'Audio & Video', 'Headphones and audio accessories', '🎧'),
            ('Home Theater Systems', 'Audio & Video', 'Home theater and surround sound systems', '🎬'),
            
            # Cameras & Photography subcategories
            ('Digital Cameras', 'Cameras & Photography', 'Digital cameras and camcorders', '📷'),
            ('Camera Lenses', 'Cameras & Photography', 'Camera lenses and optics', '🔍'),
            ('Camera Accessories', 'Cameras & Photography', 'Camera bags, tripods, and accessories', '📸'),
            
            # Computers & Laptops subcategories
            ('Desktops', 'Computers & Laptops', 'Desktop computers', '🖥️'),
            ('Laptops', 'Computers & Laptops', 'Laptop computers', '💻'),
            ('Tablets', 'Computers & Laptops', 'Tablet devices', '📱'),
            ('Computer Accessories', 'Computers & Laptops', 'Computer accessories', '⌨️'),
            
            # Home & Kitchen subcategories
            ('Appliances', 'Home & Kitchen', 'Refrigerators, stoves, dishwashers, washing machines, dryers', '🔌'),
            ('Kitchenware', 'Home & Kitchen', 'Cookware, bakeware, kitchen utensils, small appliances', '🍳'),
            ('Furniture', 'Home & Kitchen', 'Living room, bedroom, dining room, outdoor furniture', '🪑'),
            ('Home Decor', 'Home & Kitchen', 'Rugs, curtains, wall art, decorative accessories', '🖼️'),
            ('Cleaning Supplies', 'Home & Kitchen', 'Cleaning products, cleaning tools', '🧹'),
            
            # Appliances subcategories
            ('Refrigerators', 'Appliances', 'Refrigerators and freezers', '❄️'),
            ('Stoves', 'Appliances', 'Stoves and ovens', '🔥'),
            ('Dishwashers', 'Appliances', 'Dishwashers and dishwashing accessories', '🍽️'),
            ('Washing Machines', 'Appliances', 'Washing machines and laundry equipment', '🌀'),
            ('Dryers', 'Appliances', 'Dryers and drying equipment', '🌪️'),
            
            # Kitchenware subcategories
            ('Cookware', 'Kitchenware', 'Pots, pans, and cooking equipment', '🍳'),
            ('Bakeware', 'Kitchenware', 'Baking dishes and bakeware', '🥧'),
            ('Kitchen Utensils', 'Kitchenware', 'Kitchen tools and utensils', '🔪'),
            ('Small Appliances', 'Kitchenware', 'Small kitchen appliances', '⚡'),
            
            # Furniture subcategories
            ('Living Room Furniture', 'Furniture', 'Living room furniture and seating', '🛋️'),
            ('Bedroom Furniture', 'Furniture', 'Bedroom furniture and storage', '🛏️'),
            ('Dining Room Furniture', 'Furniture', 'Dining tables and chairs', '🍽️'),
            ('Outdoor Furniture', 'Furniture', 'Outdoor and patio furniture', '🌳'),
            
            # Home Decor subcategories
            ('Rugs', 'Home Decor', 'Rugs and floor coverings', '🧶'),
            ('Curtains', 'Home Decor', 'Curtains and window treatments', '🪟'),
            ('Wall Art', 'Home Decor', 'Wall art and decorations', '🖼️'),
            ('Decorative Accessories', 'Home Decor', 'Decorative items and accessories', '✨'),
            
            # Cleaning Supplies subcategories
            ('Cleaning Products', 'Cleaning Supplies', 'Cleaning solutions and chemicals', '🧴'),
            ('Cleaning Tools', 'Cleaning Supplies', 'Brooms, mops, and cleaning tools', '🧹'),
            
            # Fashion & Accessories subcategories
            ('Clothing', 'Fashion & Accessories', "Men's, women's, children's, accessories", '👔'),
            ('Footwear', 'Fashion & Accessories', 'Shoes, boots, sandals', '👟'),
            ('Jewelry', 'Fashion & Accessories', 'Necklaces, bracelets, earrings, rings', '💍'),
            ('Watches', 'Fashion & Accessories', 'Watches, watch accessories', '⌚'),
            ('Bags & Luggage', 'Fashion & Accessories', 'Handbags, backpacks, suitcases', '👜'),
            
            # Clothing subcategories
            ("Men's Clothing", 'Clothing', "Men's apparel and clothing", '👔'),
            ("Women's Clothing", 'Clothing', "Women's apparel and clothing", '👗'),
            ("Children's Clothing", 'Clothing', "Children's apparel and clothing", '👶'),
            ('Clothing Accessories', 'Clothing', 'Belts, ties, and clothing accessories', '👔'),
            
            # Footwear subcategories
            ('Shoes', 'Footwear', 'Shoes and sneakers', '👟'),
            ('Boots', 'Footwear', 'Boots and work boots', '🥾'),
            ('Sandals', 'Footwear', 'Sandals and flip-flops', '👡'),
            
            # Jewelry subcategories
            ('Necklaces', 'Jewelry', 'Necklaces and pendants', '📿'),
            ('Bracelets', 'Jewelry', 'Bracelets and bangles', '💫'),
            ('Earrings', 'Jewelry', 'Earrings and ear accessories', '💎'),
            ('Rings', 'Jewelry', 'Rings and finger jewelry', '💍'),
            
            # Watches subcategories
            ('Watches', 'Watches', 'Watches and timepieces', '⌚'),
            ('Watch Accessories', 'Watches', 'Watch bands and accessories', '⏰'),
            
            # Bags & Luggage subcategories
            ('Handbags', 'Bags & Luggage', 'Handbags and purses', '👜'),
            ('Backpacks', 'Bags & Luggage', 'Backpacks and school bags', '🎒'),
            ('Suitcases', 'Bags & Luggage', 'Luggage and travel bags', '🧳'),
            
            # Beauty & Personal Care subcategories
            ('Skincare', 'Beauty & Personal Care', 'Facial cleansers, moisturizers, serums, sunscreen', '🧴'),
            ('Makeup', 'Beauty & Personal Care', 'Foundation, eyeshadow, lipstick, blush', '💄'),
            ('Hair Care', 'Beauty & Personal Care', 'Shampoos, conditioners, styling products', '🧴'),
            ('Fragrances', 'Beauty & Personal Care', 'Perfumes, colognes', '🌸'),
            ('Grooming', 'Beauty & Personal Care', 'Razors, trimmers, shaving supplies', '✂️'),
            
            # Skincare subcategories
            ('Facial Cleansers', 'Skincare', 'Facial cleansers and face wash', '🧼'),
            ('Moisturizers', 'Skincare', 'Moisturizers and hydrating creams', '💧'),
            ('Serums', 'Skincare', 'Face serums and treatments', '✨'),
            ('Sunscreen', 'Skincare', 'Sunscreen and sun protection', '☀️'),
            
            # Makeup subcategories
            ('Foundation', 'Makeup', 'Foundation and base makeup', '💄'),
            ('Eyeshadow', 'Makeup', 'Eyeshadow and eye makeup', '👁️'),
            ('Lipstick', 'Makeup', 'Lipstick and lip products', '💋'),
            ('Blush', 'Makeup', 'Blush and cheek products', '🌸'),
            
            # Hair Care subcategories
            ('Shampoos', 'Hair Care', 'Shampoos and hair cleansers', '🧴'),
            ('Conditioners', 'Hair Care', 'Conditioners and hair treatments', '💆'),
            ('Styling Products', 'Hair Care', 'Hair styling products and tools', '💇'),
            
            # Fragrances subcategories
            ('Perfumes', 'Fragrances', 'Perfumes and fragrances', '🌸'),
            ('Colognes', 'Fragrances', 'Colognes and men\'s fragrances', '🌿'),
            
            # Grooming subcategories (Beauty & Personal Care)
            ('Razors', 'Grooming', 'Razors and shaving tools', '🪒'),
            ('Trimmers', 'Grooming', 'Hair trimmers and clippers', '✂️'),
            ('Shaving Supplies', 'Grooming', 'Shaving cream, aftershave, and supplies', '🧴'),
            
            # Health & Wellness subcategories
            ('Fitness Equipment', 'Health & Wellness', 'Exercise bikes, treadmills, dumbbells', '🏋️'),
            ('Supplements', 'Health & Wellness', 'Vitamins, minerals, protein powders', '💊'),
            ('Health Gadgets', 'Health & Wellness', 'Fitness trackers, blood pressure monitors', '📊'),
            ('Wellness Products', 'Health & Wellness', 'Yoga mats, meditation tools', '🧘'),
            ('Personal Care', 'Health & Wellness', 'Dental hygiene products, first aid supplies', '🦷'),
            
            # Fitness Equipment subcategories
            ('Exercise Bikes', 'Fitness Equipment', 'Exercise bikes and stationary bikes', '🚴'),
            ('Treadmills', 'Fitness Equipment', 'Treadmills and running equipment', '🏃'),
            ('Dumbbells', 'Fitness Equipment', 'Dumbbells and weights', '🏋️'),
            
            # Supplements subcategories
            ('Vitamins', 'Supplements', 'Vitamins and multivitamins', '💊'),
            ('Minerals', 'Supplements', 'Mineral supplements', '⚡'),
            ('Protein Powders', 'Supplements', 'Protein powders and supplements', '🥤'),
            
            # Health Gadgets subcategories
            ('Fitness Trackers', 'Health Gadgets', 'Fitness trackers and smartwatches', '⌚'),
            ('Blood Pressure Monitors', 'Health Gadgets', 'Blood pressure monitors and health devices', '🩺'),
            
            # Wellness Products subcategories
            ('Yoga Mats', 'Wellness Products', 'Yoga mats and exercise mats', '🧘'),
            ('Meditation Tools', 'Wellness Products', 'Meditation cushions and accessories', '🧘‍♀️'),
            
            # Personal Care subcategories
            ('Dental Hygiene Products', 'Personal Care', 'Toothbrushes, toothpaste, and dental care', '🦷'),
            ('First Aid Supplies', 'Personal Care', 'First aid kits and medical supplies', '🩹'),
            
            # Toys & Games subcategories
            ('Toys', 'Toys & Games', 'Stuffed animals, action figures, dolls, building toys', '🧸'),
            ('Games', 'Toys & Games', 'Board games, card games, video games, puzzles', '🎲'),
            
            # Toys subcategories
            ('Stuffed Animals', 'Toys', 'Stuffed animals and plush toys', '🧸'),
            ('Action Figures', 'Toys', 'Action figures and collectibles', '🤖'),
            ('Dolls', 'Toys', 'Dolls and doll accessories', '👸'),
            ('Building Toys', 'Toys', 'Building blocks and construction toys', '🧱'),
            
            # Games subcategories
            ('Board Games', 'Games', 'Board games for all ages', '🎲'),
            ('Card Games', 'Games', 'Card games and playing cards', '🃏'),
            ('Video Games', 'Games', 'Video games and gaming accessories', '🎮'),
            ('Puzzles', 'Games', 'Jigsaw puzzles and brain teasers', '🧩'),
            
            # Sports & Outdoors subcategories
            ('Sports Equipment', 'Sports & Outdoors', 'Exercise equipment, team sports equipment, individual sports equipment', '⚽'),
            ('Outdoor Gear', 'Sports & Outdoors', 'Camping equipment, hiking gear, fishing supplies, gardening tools', '🏕️'),
            ('Outdoor Toys', 'Sports & Outdoors', 'Trampolines, swings, slides', '🛝'),
            
            # Sports Equipment subcategories
            ('Exercise Equipment', 'Sports Equipment', 'Exercise and fitness equipment', '🏋️'),
            ('Team Sports Equipment', 'Sports Equipment', 'Team sports gear and equipment', '⚽'),
            ('Individual Sports Equipment', 'Sports Equipment', 'Individual sports gear and equipment', '🎾'),
            
            # Outdoor Gear subcategories
            ('Camping Equipment', 'Outdoor Gear', 'Camping gear and supplies', '⛺'),
            ('Hiking Gear', 'Outdoor Gear', 'Hiking and backpacking equipment', '🥾'),
            ('Fishing Supplies', 'Outdoor Gear', 'Fishing gear and supplies', '🎣'),
            ('Gardening Tools', 'Outdoor Gear', 'Gardening tools and supplies', '🌱'),
            
            # Outdoor Toys subcategories
            ('Trampolines', 'Outdoor Toys', 'Trampolines and jumping equipment', '🤸'),
            ('Swings', 'Outdoor Toys', 'Swings and playground equipment', '🛝'),
            ('Slides', 'Outdoor Toys', 'Slides and playground equipment', '🛝'),
            
            # Books & Movies subcategories
            ('Books', 'Books & Movies', 'Fiction, non-fiction, children\'s books', '📚'),
            ('Movies', 'Books & Movies', 'Blu-ray, DVD, digital downloads', '🎬'),
            ('TV Shows', 'Books & Movies', 'DVDs, digital downloads', '📺'),
            
            # Books subcategories
            ('Fiction', 'Books', 'Fiction books and novels', '📖'),
            ('Non-Fiction', 'Books', 'Non-fiction books and reference', '📚'),
            ("Children's Books", 'Books', "Children's books and picture books", '👶'),
            
            # Movies subcategories
            ('Blu-ray', 'Movies', 'Blu-ray movies and discs', '💿'),
            ('DVD', 'Movies', 'DVD movies and discs', '💿'),
            ('Digital Downloads', 'Movies', 'Digital movie downloads', '📥'),
            
            # TV Shows subcategories
            ('TV Show DVDs', 'TV Shows', 'TV show DVDs and box sets', '💿'),
            ('TV Show Digital Downloads', 'TV Shows', 'Digital TV show downloads', '📥'),
            
            # Automotive subcategories
            ('Vehicles', 'Automotive', 'Cars, trucks, motorcycles', '🚗'),
            ('Parts & Accessories', 'Automotive', 'Tires, batteries, engine parts', '🔧'),
            ('Automotive Tools', 'Automotive', 'Wrenches, screwdrivers, jacks', '🛠️'),
            
            # Vehicles subcategories
            ('Cars', 'Vehicles', 'Cars and automobiles', '🚗'),
            ('Trucks', 'Vehicles', 'Trucks and pickup trucks', '🚚'),
            ('Motorcycles', 'Vehicles', 'Motorcycles and bikes', '🏍️'),
            
            # Parts & Accessories subcategories
            ('Tires', 'Parts & Accessories', 'Tires and wheels', '⭕'),
            ('Batteries', 'Parts & Accessories', 'Car batteries and electrical', '🔋'),
            ('Engine Parts', 'Parts & Accessories', 'Engine parts and components', '⚙️'),
            
            # Automotive Tools subcategories
            ('Wrenches', 'Automotive Tools', 'Wrenches and hand tools', '🔧'),
            ('Screwdrivers', 'Automotive Tools', 'Screwdrivers and drivers', '🪛'),
            ('Jacks', 'Automotive Tools', 'Jacks and lifting equipment', '🔩'),
            
            # Pet Supplies subcategories
            ('Food', 'Pet Supplies', 'Dog food, cat food, pet treats', '🍖'),
            ('Accessories', 'Pet Supplies', 'Collars, leashes, toys', '🎾'),
            ('Grooming', 'Pet Supplies', 'Brushes, shampoos, grooming tools', '✂️'),
            ('Health', 'Pet Supplies', 'Medications, supplements', '💊'),
            
            # Food subcategories
            ('Dog Food', 'Food', 'Dog food and dog nutrition', '🐕'),
            ('Cat Food', 'Food', 'Cat food and cat nutrition', '🐱'),
            ('Pet Treats', 'Food', 'Pet treats and snacks', '🍖'),
            
            # Accessories subcategories (Pet Supplies)
            ('Collars', 'Accessories', 'Pet collars and tags', '🐕'),
            ('Leashes', 'Accessories', 'Pet leashes and leads', '🦮'),
            ('Pet Toys', 'Accessories', 'Pet toys and playthings', '🎾'),
            
            # Grooming subcategories (Pet Supplies)
            ('Pet Brushes', 'Grooming', 'Pet brushes and combs', '🪮'),
            ('Pet Shampoos', 'Grooming', 'Pet shampoos and grooming products', '🧴'),
            ('Grooming Tools', 'Grooming', 'Pet grooming tools and accessories', '✂️'),
            
            # Health subcategories
            ('Pet Medications', 'Health', 'Pet medications and prescriptions', '💊'),
            ('Pet Supplements', 'Health', 'Pet supplements and vitamins', '💊'),
        ]
        
        # Create a mapping of (name, parent_name) to category objects
        # Use (name, parent_name) as key to handle duplicate names under different parents
        parent_map = {}
        
        # First pass: Create all top-level categories
        for name, parent_name, description, icon in categories_data:
            if parent_name is None:
                slug = slugify(name)
                category = get_or_create_category(name, slug, None, description, icon)
                # Store with key (name, None) for top-level
                parent_map[(name, None)] = category
                print(f'  Created/Updated top-level: {name}')
        
        # Second pass: Create all subcategories (multiple passes for nested categories)
        max_depth = 10  # Safety limit
        for depth in range(max_depth):
            created_any = False
            for name, parent_name, description, icon in categories_data:
                if parent_name is not None:
                    # Check if this category already exists in parent_map
                    key = (name, parent_name)
                    if key in parent_map:
                        continue  # Already processed
                    
                    # Try to find parent
                    parent_key = (parent_name, None) if parent_name in [cat[0] for cat in categories_data if cat[1] is None] else None
                    if parent_key is None:
                        # Parent might be a subcategory, search for it
                        for pname, pparent in parent_map.keys():
                            if pname == parent_name:
                                parent_key = (pname, pparent)
                                break
                    
                    if parent_key and parent_key in parent_map:
                        parent_category = parent_map[parent_key]
                        slug = slugify(name)
                        category = get_or_create_category(name, slug, parent_category.id, description, icon)
                        parent_map[key] = category
                        print(f'  Created/Updated subcategory: {name} (parent: {parent_name})')
                        created_any = True
                    elif parent_name in [cat[0] for cat in categories_data if cat[1] is None]:
                        # Parent is top-level
                        parent_key = (parent_name, None)
                        if parent_key in parent_map:
                            parent_category = parent_map[parent_key]
                            slug = slugify(name)
                            category = get_or_create_category(name, slug, parent_category.id, description, icon)
                            parent_map[key] = category
                            print(f'  Created/Updated subcategory: {name} (parent: {parent_name})')
                            created_any = True
                        else:
                            print(f'  WARNING: Parent "{parent_name}" not found for "{name}"')
                    # If parent not found yet, it will be processed in next iteration
            
            if not created_any:
                break  # No more categories to create
        
        print('\n✓ Subcategories seeded successfully!')


if __name__ == '__main__':
    seed_subcategories()

