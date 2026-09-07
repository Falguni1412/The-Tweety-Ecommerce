import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import (
    User, Address, Category, Product, ProductVariant,
    ProductAttribute, AttributeOption, ProductSpecification,
    Review, Coupon, Wishlist, WishlistItem,
    Cart, CartItem, Payment, Order, OrderItem, OrderTracking
)


def make_slug(text):
    return text.lower().replace(' ', '-').replace('&', 'and').replace("'", '')


class Command(BaseCommand):
    help = "Reset database and seed with comprehensive demo data"

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database...')

        # ===== 1. CLEAR EXISTING DATA =====
        self.stdout.write('  Clearing existing data...')
        OrderItem.objects.all().delete()
        OrderTracking.objects.all().delete()
        Order.objects.all().delete()
        Payment.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        WishlistItem.objects.all().delete()
        Wishlist.objects.all().delete()
        Coupon.objects.all().delete()
        Review.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductSpecification.objects.all().delete()
        Product.objects.all().delete()
        ProductAttribute.objects.all().delete()
        AttributeOption.objects.all().delete()
        Address.objects.all().delete()
        User.objects.all().delete()
        Category.objects.all().delete()

        # ===== 2. CREATE CATEGORIES =====
        self.stdout.write('  Creating categories...')
        cats = [
            ('electronics', 'Electronics', 'Laptops, phones, tablets & more', 1),
            ('smartphones', 'Smartphones', 'Flagship & budget smartphones', 2),
            ('laptops', 'Laptops', 'Gaming, business & student laptops', 3),
            ('audio', 'Audio & Headphones', 'Wireless earbuds, headphones, speakers', 4),
            ('wearables', 'Wearables', 'Smartwatches & fitness trackers', 5),
            ('cameras', 'Cameras & Photography', 'DSLR, mirrorless & action cameras', 6),
            ('mens-fashion', "Men's Fashion", 'Clothing, footwear & accessories', 7),
            ('womens-fashion', "Women's Fashion", 'Ethnic, western & fusion wear', 8),
            ('footwear', 'Footwear', 'Sports, casual & formal shoes', 9),
            ('home-kitchen', 'Home & Kitchen', 'Appliances, decor & furnishing', 10),
            ('sports-fitness', 'Sports & Fitness', 'Equipment, supplements & gear', 11),
            ('books', 'Books', 'Fiction, non-fiction & study material', 12),
        ]
        cat_map = {}
        for slug, name, desc, order in cats:
            c = Category.objects.create(
                slug=slug, name=name, description=desc, display_order=order
            )
            cat_map[slug] = c

        # ===== 3. CREATE PRODUCT ATTRIBUTES =====
        self.stdout.write('  Creating attributes...')
        color_attr = ProductAttribute.objects.create(
            name='Color', slug='color', attribute_type='color', display_order=1
        )
        size_attr = ProductAttribute.objects.create(
            name='Size', slug='size', attribute_type='text', display_order=2
        )
        ram_attr = ProductAttribute.objects.create(
            name='RAM', slug='ram', attribute_type='text', display_order=3
        )
        storage_attr = ProductAttribute.objects.create(
            name='Storage', slug='storage', attribute_type='text', display_order=4
        )

        # Color options
        color_options = {
            'Midnight Black': '#1a1a1a',
            'Starlight': '#f5f0e8',
            'Space Gray': '#6e6e73',
            'Pacific Blue': '#3a5a7c',
            'Deep Purple': '#5b2c6f',
            'Coral Pink': '#f1948a',
            'Emerald Green': '#1e8449',
            'Navy Blue': '#1b4f72',
            'Carbon Gray': '#424949',
            'Phantom Black': '#17202a',
            'Sunset Orange': '#e67e22',
            'Mint Green': '#76d7c4',
        }
        color_opts = {}
        for name, code in color_options.items():
            o = AttributeOption.objects.create(
                attribute=color_attr, value=name,
                slug=make_slug(name), color_code=code
            )
            color_opts[name] = o

        # Size options
        size_opts = {}
        for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
            o = AttributeOption.objects.create(
                attribute=size_attr, value=size, slug=make_slug(size)
            )
            size_opts[size] = o

        # RAM options
        ram_opts = {}
        for ram in ['4GB', '8GB', '16GB', '32GB']:
            o = AttributeOption.objects.create(
                attribute=ram_attr, value=ram, slug=make_slug(ram)
            )
            ram_opts[ram] = o

        # Storage options
        storage_opts = {}
        for storage in ['128GB', '256GB', '512GB', '1TB']:
            o = AttributeOption.objects.create(
                attribute=storage_attr, value=storage, slug=make_slug(storage)
            )
            storage_opts[storage] = o

        # ===== 4. CREATE PRODUCTS =====
        self.stdout.write('  Creating products...')
        products_created = []

        def create_product(title, brand, cat_slug, price, disc_price, desc,
                          stock=50, rating=4.5, reviews=50,
                          featured=False, bestseller=False, new=False,
                          specs=None, variants=None, tags=None):
            p = Product.objects.create(
                title=title, brand=brand, category=cat_map[cat_slug],
                selling_price=price, discounted_price=disc_price,
                description=desc, stock=stock, rating=rating,
                num_reviews=reviews, is_featured=featured,
                is_bestseller=bestseller, is_new=new,
                free_delivery=True, cash_on_delivery=True,
                tags=tags or [],
            )
            if specs:
                for i, (name, val) in enumerate(specs):
                    ProductSpecification.objects.create(
                        product=p, spec_name=name, spec_value=val, display_order=i
                    )
            if variants:
                for vdata in variants:
                    v = ProductVariant.objects.create(
                        product=p, stock=vdata.get('stock', 20),
                        price=vdata.get('price', disc_price),
                        compare_price=vdata.get('compare', price),
                        sku=f"SKU-{p.id}-{vdata['attrs'][0][:2] if vdata['attrs'] else '00'}",
                    )
                    for attr_name in vdata['attrs']:
                        if attr_name in color_opts:
                            v.attribute_values.create(
                                attribute=color_attr, option=color_opts[attr_name]
                            )
                        elif attr_name in size_opts:
                            v.attribute_values.create(
                                attribute=size_attr, option=size_opts[attr_name]
                            )
                        elif attr_name in ram_opts:
                            v.attribute_values.create(
                                attribute=ram_attr, option=ram_opts[attr_name]
                            )
                        elif attr_name in storage_opts:
                            v.attribute_values.create(
                                attribute=storage_attr, option=storage_opts[attr_name]
                            )
            products_created.append(p)
            return p

        # --- Electronics ---
        create_product(
            'iPhone 15 Pro Max', 'Apple', 'smartphones',
            159900, 139900,
            'iPhone 15 Pro Max features the most powerful iPhone camera system ever. '
            'A17 Pro chip delivers incredible performance. Titanium design makes it '
            'lightweight yet durable. Action Button gives instant access to your favorite feature.',
            stock=30, rating=4.9, reviews=342,
            featured=True, bestseller=True, new=False,
            specs=[
                ('Display', '6.7-inch Super Retina XDR'),
                ('Chip', 'A17 Pro'),
                ('Camera', '48MP Main + 12MP Ultra Wide + 12MP Telephoto'),
                ('Battery', 'Up to 29 hours video playback'),
                ('Connectivity', '5G, Wi-Fi 6E, Bluetooth 5.3'),
                ('Water Resistance', 'IP68'),
            ],
            variants=[
                {'attrs': ['Natural Titanium'], 'price': 139900, 'compare': 159900, 'stock': 10},
                {'attrs': ['Blue Titanium'], 'price': 139900, 'compare': 159900, 'stock': 8},
                {'attrs': ['White Titanium'], 'price': 139900, 'compare': 159900, 'stock': 7},
                {'attrs': ['Black Titanium'], 'price': 139900, 'compare': 159900, 'stock': 5},
            ],
            tags=['iphone', 'apple', 'flagship', '5g', 'smartphone']
        )

        create_product(
            'Samsung Galaxy S24 Ultra', 'Samsung', 'smartphones',
            129999, 114999,
            'Galaxy AI is here. Galaxy S24 Ultra transforms your mobile experience with AI-powered '
            'camera, real-time translation, and Circle to Search. 200MP camera captures incredible detail.',
            stock=25, rating=4.7, reviews=189,
            featured=True, bestseller=True, new=False,
            specs=[
                ('Display', '6.8-inch Dynamic AMOLED 2X'),
                ('Chip', 'Snapdragon 8 Gen 3'),
                ('Camera', '200MP Main + 50MP Periscope + 12MP Ultra Wide'),
                ('Battery', '5000mAh'),
                ('S Pen', 'Built-in S Pen'),
            ],
            variants=[
                {'attrs': ['Titanium Black'], 'price': 114999, 'compare': 129999, 'stock': 10},
                {'attrs': ['Titanium Gray'], 'price': 114999, 'compare': 129999, 'stock': 8},
                {'attrs': ['Titanium Violet'], 'price': 114999, 'compare': 129999, 'stock': 7},
                {'attrs': ['Titanium Yellow'], 'price': 114999, 'compare': 129999, 'stock': 5},
            ],
            tags=['samsung', 'galaxy', 'android', 'ai', 'flagship']
        )

        create_product(
            'MacBook Air M3 15-inch', 'Apple', 'laptops',
            134900, 114900,
            'Supercharged by the M3 chip, MacBook Air 15-inch delivers exceptional performance '
            'for demanding workflows. Fanless design means it stays completely silent. '
            'All-day battery life up to 18 hours.',
            stock=15, rating=4.8, reviews=156,
            featured=True, bestseller=False, new=True,
            specs=[
                ('Chip', 'Apple M3 (8-core CPU, 10-core GPU)'),
                ('Memory', '8GB Unified Memory'),
                ('Storage', '256GB SSD'),
                ('Display', '15.3-inch Liquid Retina'),
                ('Battery', 'Up to 18 hours'),
                ('Weight', '1.51 kg'),
            ],
            variants=[
                {'attrs': ['Midnight Black'], 'price': 114900, 'compare': 134900, 'stock': 5},
                {'attrs': ['Space Gray'], 'price': 114900, 'compare': 134900, 'stock': 5},
                {'attrs': ['Starlight'], 'price': 114900, 'compare': 134900, 'stock': 5},
            ],
            tags=['macbook', 'apple', 'laptop', 'm3', 'thin']
        )

        create_product(
            'Sony WH-1000XM5 Wireless Headphones', 'Sony', 'audio',
            34990, 24990,
            'Industry-leading noise cancellation with Auto NC Optimizer. Exceptional sound quality '
            'with 30mm driver unit. Crystal clear hands-free calling with 4 beamforming microphones.',
            stock=40, rating=4.8, reviews=567,
            featured=True, bestseller=True, new=False,
            specs=[
                ('Driver', '30mm'),
                ('Frequency Response', '4 Hz - 40,000 Hz'),
                ('Battery Life', 'Up to 30 hours'),
                ('Noise Cancellation', 'Auto NC Optimizer'),
                ('Quick Charge', '3 hours playback from 3-min charge'),
            ],
            tags=['sony', 'headphones', 'noise cancelling', 'wireless', 'premium']
        )

        create_product(
            'AirPods Pro 2nd Generation', 'Apple', 'audio',
            24999, 19999,
            'Active Noise Cancellation reduces unwanted background noise. Adaptive Transparency '
            'lets outside sounds in while reducing loud environmental noise.',
            stock=60, rating=4.7, reviews=892,
            featured=True, bestseller=True, new=False,
            specs=[
                ('Chip', 'Apple H2'),
                ('Active Noise Cancellation', 'Yes'),
                ('Adaptive Transparency', 'Yes'),
                ('Spatial Audio', 'Personalized with dynamic head tracking'),
                ('Battery', 'Up to 6 hours (30 hours with case)'),
                ('Water Resistance', 'IPX4'),
            ],
            tags=['airpods', 'apple', 'earbuds', 'wireless', 'anc']
        )

        create_product(
            'Samsung Galaxy Watch 6 Classic', 'Samsung', 'wearables',
            32999, 26999,
            'The classic rotating bezel returns. Track your health with advanced sleep analysis, '
            'body composition, and ECG. Sapphire crystal glass ensures durability.',
            stock=35, rating=4.6, reviews=234,
            featured=False, bestseller=True, new=False,
            specs=[
                ('Display', '1.5-inch Super AMOLED'),
                ('Processor', 'Exynos W930'),
                ('Storage', '16GB'),
                ('Battery', 'Up to 40 hours'),
                ('Water Resistance', '5ATM + IP68'),
                ('GPS', 'Dual-frequency GPS'),
            ],
            tags=['samsung', 'smartwatch', 'wearable', 'fitness', 'galaxy']
        )

        create_product(
            'Apple Watch Ultra 2', 'Apple', 'wearables',
            89900, 79900,
            'The most rugged and capable Apple Watch. Built for endurance, exploration, '
            'and adventure. 49mm titanium case. Up to 36 hours of battery life.',
            stock=10, rating=4.9, reviews=89,
            featured=True, bestseller=False, new=True,
            specs=[
                ('Case', '49mm Titanium'),
                ('Display', '2000 nits peak brightness'),
                ('Chip', 'S9 SiP'),
                ('Battery', 'Up to 36 hours'),
                ('Water Resistance', '100m'),
                ('GPS', 'Precision dual-frequency GPS'),
            ],
            tags=['apple', 'watch', 'ultra', 'rugged', 'adventure']
        )

        create_product(
            'Canon EOS R6 Mark II', 'Canon', 'cameras',
            249995, 219995,
            'Full-frame mirrorless camera with 40fps continuous shooting. '
            '4K 60fps video recording. Built-in image stabilization up to 8 stops.',
            stock=8, rating=4.8, reviews=67,
            featured=False, bestseller=False, new=True,
            specs=[
                ('Sensor', '24.2MP Full-Frame CMOS'),
                ('ISO Range', '100-102400 (expandable)'),
                ('Continuous Shooting', 'Up to 40fps (electronic)'),
                ('Video', '4K 60fps, 6K RAW external'),
                ('Stabilization', '8-stop IBIS'),
                ('AF Points', '1053 zones'),
            ],
            tags=['canon', 'camera', 'mirrorless', 'full-frame', 'video']
        )

        create_product(
            'boAt Rockerz 551 ANC', 'boAt', 'audio',
            4999, 2499,
            'Active Noise Cancellation up to 35dB. 100 hours of playtime. ASAP Charge '
            'technology gives 10 hours of playback in just 10 minutes.',
            stock=100, rating=4.3, reviews=1245,
            featured=False, bestseller=True, new=False,
            specs=[
                ('Driver', '40mm'),
                ('Battery', 'Up to 100 hours'),
                ('ANC', 'Up to 35dB'),
                ('Quick Charge', '10 min charge = 10 hours'),
                ('Bluetooth', '5.3'),
            ],
            tags=['boat', 'headphones', 'wireless', 'anc', 'budget']
        )

        # --- Fashion ---
        create_product(
            "Men's Premium Cotton Formal Shirt", 'Louis Philippe', 'mens-fashion',
            1999, 999,
            'Premium cotton fabric with a modern slim fit. Wrinkle-resistant technology '
            'keeps you looking sharp all day. Perfect for office and formal occasions.',
            stock=200, rating=4.4, reviews=456,
            featured=False, bestseller=False, new=False,
            specs=[('Material', '100% Premium Cotton'), ('Fit', 'Slim Fit'), ('Pattern', 'Solid')],
            variants=[
                {'attrs': ['White'], 'stock': 50},
                {'attrs': ['Light Blue'], 'stock': 50},
                {'attrs': ['Black'], 'stock': 50},
                {'attrs': ['Pink'], 'stock': 50},
            ] + [{'attrs': [size]} for size in ['S', 'M', 'L', 'XL', 'XXL']],
            tags=['shirt', 'formal', 'men', 'cotton', 'office']
        )

        create_product(
            "Women's Embroidered Kurta Set", 'Libas', 'womens-fashion',
            3999, 2499,
            'Beautiful ethnic kurta with intricate embroidery. Comes with matching bottom. '
            'Perfect for festivals, weddings, and special occasions.',
            stock=80, rating=4.5, reviews=234,
            featured=True, bestseller=True, new=False,
            specs=[('Material', 'Crepe'), ('Pattern', 'Embroidered'), ('Occasion', 'Ethnic')],
            variants=[
                {'attrs': ['Emerald Green'], 'stock': 20},
                {'attrs': ['Navy Blue'], 'stock': 20},
                {'attrs': ['Coral Pink'], 'stock': 20},
                {'attrs': ['Sunset Orange'], 'stock': 20},
            ] + [{'attrs': [size]} for size in ['S', 'M', 'L', 'XL']],
            tags=['kurta', 'ethnic', 'women', 'embroidered', 'festive']
        )

        create_product(
            'Nike Air Max 270 Running Shoes', 'Nike', 'footwear',
            11995, 7995,
            'The Nike Air Max 270 delivers visible cushioning under every step. '
            'Lightweight mesh upper keeps you cool. Max Air unit provides all-day comfort.',
            stock=150, rating=4.6, reviews=678,
            featured=True, bestseller=True, new=False,
            specs=[('Upper', 'Mesh'), ('Cushioning', 'Max Air'), ('Sole', 'Rubber')],
            variants=[
                {'attrs': ['Black Titanium'], 'stock': 30},
                {'attrs': ['White Titanium'], 'stock': 30},
                {'attrs': ['Midnight Black'], 'stock': 30},
                {'attrs': ['Carbon Gray'], 'stock': 30},
            ] + [{'attrs': [size]} for size in ['7', '8', '9', '10', '11']],
            tags=['nike', 'shoes', 'running', 'air max', 'sports']
        )

        # --- Home & Kitchen ---
        create_product(
            'Instant Pot Duo 7-in-1 Electric Pressure Cooker', 'Instant Pot', 'home-kitchen',
            8999, 6499,
            '7 appliances in 1: pressure cooker, slow cooker, rice cooker, steamer, '
            'sauté pan, yogurt maker, and warmer. 6-quart capacity serves up to 6 people.',
            stock=45, rating=4.7, reviews=1234,
            featured=True, bestseller=True, new=False,
            specs=[
                ('Capacity', '6 Quarts'),
                ('Functions', '7-in-1'),
                ('Pressure Settings', 'High/Low'),
                ('Delay Timer', 'Up to 24 hours'),
                ('Keep Warm', 'Up to 10 hours'),
            ],
            tags=['instant pot', 'pressure cooker', 'kitchen', 'multi-cooker', 'appliance']
        )

        create_product(
            'Milton Thermosteel Flip Lid Flask 1L', 'Milton', 'home-kitchen',
            999, 599,
            'Double-wall vacuum insulation keeps water cold for 24 hours or hot for 12 hours. '
            'BPA-free, leak-proof design. Fits most car cup holders.',
            stock=300, rating=4.5, reviews=2341,
            featured=False, bestseller=True, new=False,
            specs=[('Capacity', '1 Litre'), ('Material', 'Stainless Steel'), ('Insulation', 'Double-wall Vacuum')],
            variants=[
                {'attrs': ['Midnight Black'], 'stock': 75},
                {'attrs': ['Starlight'], 'stock': 75},
                {'attrs': ['Coral Pink'], 'stock': 75},
                {'attrs': ['Navy Blue'], 'stock': 75},
            ],
            tags=['flask', 'water bottle', 'thermos', 'insulated', 'bpa-free']
        )

        # --- Sports ---
        create_product(
            'HRX Performance Resistance Bands Set', 'HRX', 'sports-fitness',
            1499, 899,
            'Set of 5 resistance bands with different tension levels. Perfect for '
            'strength training, physical therapy, and warm-ups. Includes door anchor and handles.',
            stock=200, rating=4.4, reviews=1567,
            featured=False, bestseller=True, new=False,
            tags=['resistance bands', 'fitness', 'home workout', 'training', 'exercise']
        )

        # --- Books ---
        book_product = create_product(
            'Atomic Habits by James Clear', 'Penguin Random House', 'books',
            699, 499,
            'No matter your goals, Atomic Habits offers a proven framework for improving '
            'every day. James Clear reveals practical strategies that will teach you '
            'exactly how to form good habits and break bad ones.',
            stock=500, rating=4.8, reviews=4500,
            featured=True, bestseller=True, new=False,
            specs=[('Author', 'James Clear'), ('Pages', '320'), ('Publisher', 'Avery Publishing')],
            tags=['self-help', 'habits', 'productivity', 'bestseller', 'psychology']
        )

        create_product(
            'The Psychology of Money', 'Harriman House', 'books',
            499, 349,
            'Timeless lessons on wealth, greed, and happiness. Morgan Housel shares 19 '
            'short stories exploring the strange ways people think about money.',
            stock=400, rating=4.7, reviews=3200,
            featured=False, bestseller=True, new=False,
            tags=['finance', 'money', 'investing', 'bestseller', 'psychology']
        )

        # ===== 5. CREATE REVIEWS =====
        self.stdout.write('  Creating reviews...')
        review_titles = [
            'Excellent product!', 'Highly recommended', 'Great value for money',
            'Amazing quality', 'Worth every penny', 'Good but pricey',
            'Perfect for my needs', 'Better than expected', 'Could be better',
            'Outstanding performance', 'Must buy!', 'Decent product',
        ]
        review_comments = [
            'The product quality is excellent. Delivery was super fast. Highly recommended!',
            'Good product but packaging could be better. Overall satisfied with the purchase.',
            'Amazing value for money. Works exactly as described. Would buy again.',
            'This has become my go-to product. Quality is top-notch.',
            'Worth the investment. My second purchase and still impressed.',
            'Delivery was delayed by 2 days but the product itself is great.',
            'Perfect for daily use. Compact and easy to carry around.',
            'Exceeded my expectations. The build quality is premium.',
            'Good product at this price point. Some minor issues but overall okay.',
            'Outstanding! Best purchase I made this year.',
        ]

        for p in products_created[:8]:
            num_reviews = min(random.randint(3, 8), p.num_reviews // 10 + 1)
            for i in range(num_reviews):
                Review.objects.create(
                    product=p,
                    user=User.objects.first(),  # will create demo user first
                    rating=random.randint(3, 5),
                    title=random.choice(review_titles),
                    comment=random.choice(review_comments),
                    verification_status='verified',
                    helpful_count=random.randint(0, 50),
                )

        # ===== 6. CREATE DEMO USER =====
        self.stdout.write('  Creating demo user...')
        demo_user = User.objects.create(
            username='demo', password='demo123', email='demo@shopify.com', phone='9876543210'
        )
        Address.objects.create(
            user=demo_user, name='Demo User', locality='123 Main Street',
            city='Mumbai', pincode=400001, state='Maharashtra', phone='9876543210',
            is_default=True, address_type='home'
        )
        Address.objects.create(
            user=demo_user, name='Demo User', locality='456 Office Park, Andheri West',
            city='Mumbai', pincode=400053, state='Maharashtra', phone='9876543210',
            is_default=False, address_type='work'
        )

        # ===== 7. CREATE COUPONS =====
        self.stdout.write('  Creating coupons...')
        coupons_data = [
            ('FIRST100', 'First Order Discount', 'flat', 100, 0, None, 500),
            ('SAVE20', '20% Off on Everything', 'percent', 20, 0, 2000, 1000),
            ('TECH15', '15% Off on Electronics', 'percent', 15, 0, 1000, 500),
            ('FLAT200', 'Flat ₹200 Off', 'flat', 200, 0, 1000, 500),
            ('FREESHIP', 'Free Delivery', 'free_shipping', 0, 0, None, 200),
            ('BOOGO', 'Buy 1 Get 1 Free', 'bogo', 0, 0, None, 50),
        ]
        for code, title, dtype, value, min_ord, max_disc, usage in coupons_data:
            Coupon.objects.create(
                code=code, title=title, discount_type=dtype,
                discount_value=value, min_order_amount=min_ord,
                max_discount=max_disc, usage_limit=usage,
                valid_from=timezone.now() - timedelta(days=1),
                valid_until=timezone.now() + timedelta(days=365),
                is_active=True,
            )

        # ===== 8. CREATE SAMPLE ORDERS FOR DEMO USER =====
        self.stdout.write('  Creating sample orders...')
        product_list = list(Product.objects.all()[:6])
        if product_list:
            cart = Cart.objects.create(user=demo_user)
            for prod in product_list[:3]:
                CartItem.objects.create(
                    cart=cart, product=prod,
                    quantity=random.randint(1, 2)
                )
            subtotal = cart.get_subtotal()
            shipping = 0 if subtotal > 500 else 49
            tax = round(subtotal * 0.05, 2)

            # Create completed order
            order = Order.objects.create(
                user=demo_user,
                shipping_address=demo_user.addresses.first(),
                subtotal=subtotal, shipping_cost=shipping, tax_amount=tax,
                total_price=subtotal + shipping + tax,
                status='delivered',
                expected_delivery=timezone.now().date() - timedelta(days=2),
                confirmed_at=timezone.now() - timedelta(days=7),
            )
            for item in cart.items.all():
                order.items.add(item)
                OrderItem.objects.create(
                    order=order,
                    product_title=item.product.title,
                    product_brand=item.product.brand,
                    product_image=item.product.product_image,
                    price=item.get_unit_price(),
                    quantity=item.quantity,
                    total=item.get_total(),
                )

            # Add tracking events
            OrderTracking.objects.create(
                order=order, status='pending', title='Order Placed',
                description='Your order has been confirmed.',
                is_completed=True, timestamp=timezone.now() - timedelta(days=7)
            )
            OrderTracking.objects.create(
                order=order, status='confirmed', title='Payment Confirmed',
                description='Payment of ₹' + str(order.total_price) + ' received.',
                is_completed=True, timestamp=timezone.now() - timedelta(days=7)
            )
            OrderTracking.objects.create(
                order=order, status='processing', title='Order Processing',
                description='Your order is being prepared for shipment.',
                is_completed=True, timestamp=timezone.now() - timedelta(days=6)
            )
            OrderTracking.objects.create(
                order=order, status='shipped', title='Order Shipped',
                description='Your order has been shipped via BlueDart Express.',
                location='Mumbai Warehouse',
                is_completed=True, timestamp=timezone.now() - timedelta(days=5)
            )
            OrderTracking.objects.create(
                order=order, status='out_for_delivery', title='Out for Delivery',
                description='Your order is out for delivery. Expected by 6 PM.',
                location='Mumbai Delivery Center',
                is_completed=True, timestamp=timezone.now() - timedelta(days=3)
            )
            OrderTracking.objects.create(
                order=order, status='delivered', title='Delivered',
                description='Your order has been delivered successfully.',
                location='Mumbai',
                is_completed=True, timestamp=timezone.now() - timedelta(days=2)
            )

            Payment.objects.create(
                user=demo_user, order=order, payment_type='card',
                amount=order.total_price, status='completed',
                card_last_four='4532', card_holder='Demo User',
                card_type='Visa', completed_at=timezone.now() - timedelta(days=7)
            )

            cart.items.all().delete()

        # ===== 9. CREATE WISHLIST =====
        self.stdout.write('  Creating wishlist...')
        wishlist, _ = Wishlist.objects.get_or_create(user=demo_user)
        for prod in Product.objects.filter(is_featured=True)[:5]:
            WishlistItem.objects.get_or_create(wishlist=wishlist, product=prod)

        # ===== SUMMARY =====
        total_products = Product.objects.count()
        total_reviews = Review.objects.count()
        total_coupons = Coupon.objects.count()
        total_orders = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seeding complete!\n'
            f'   Categories: {Category.objects.count()}\n'
            f'   Products: {total_products}\n'
            f'   Variants: {ProductVariant.objects.count()}\n'
            f'   Reviews: {total_reviews}\n'
            f'   Demo User: demo / demo123\n'
            f'   Coupons: {total_coupons}\n'
            f'   Orders: {total_orders}\n'
        ))
