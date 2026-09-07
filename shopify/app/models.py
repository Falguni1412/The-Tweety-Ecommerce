import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


# ============================================================
# User & Address (existing)
# ============================================================
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # increased for hashed passwords
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=40)
    locality = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    pincode = models.IntegerField()
    state = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True, default='')
    is_default = models.BooleanField(default=False)
    address_type = models.CharField(max_length=20, choices=[
        ('home', 'Home'), ('work', 'Work'), ('other', 'Other')
    ], default='home')

    def __str__(self):
        return f"{self.name}, {self.city}"


# ============================================================
# Category
# ============================================================
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_product_count(self):
        return self.products.filter(is_active=True).count()


# ============================================================
# Product Attribute System
# ============================================================
class ProductAttribute(models.Model):
    """Global attribute definitions like Color, Size, RAM, Storage"""
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    attribute_type = models.CharField(max_length=20, choices=[
        ('color', 'Color (with swatch)'),
        ('text', 'Text'),
        ('swatch', 'Swatch/Patterened'),
    ], default='text')
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Product Attributes"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class AttributeOption(models.Model):
    """Predefined options for an attribute, e.g., Red, Blue for Color"""
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)  # "Red", "256GB"
    slug = models.SlugField()
    color_code = models.CharField(max_length=7, blank=True, default='')  # hex for color swatches
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'value']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ============================================================
# Products
# ============================================================
class Product(models.Model):
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Litre'),
        ('ml', 'Millilitre'),
        ('m', 'Metre'),
        ('box', 'Box'),
        ('pack', 'Pack'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)
    product_images = models.JSONField(default=list, blank=True)  # additional image URLs
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    rating = models.FloatField(default=0.0)
    num_reviews = models.IntegerField(default=0)
    num_sold = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    free_delivery = models.BooleanField(default=True)
    cash_on_delivery = models.BooleanField(default=True)
    return_days = models.IntegerField(default=7)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)[:50]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def discount_percent(self):
        if self.selling_price > 0:
            return int((self.selling_price - self.discounted_price) / self.selling_price * 100)
        return 0

    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    def is_out_of_stock(self):
        return self.stock <= 0

    def get_variant_count(self):
        return self.variants.count()

    def get_min_price(self):
        """Minimum price across all variants"""
        min_var = self.variants.aggregate(min=models.Min('price'))['min']
        return min_var if min_var is not None else float(self.discounted_price)

    def get_max_price(self):
        """Maximum price across all variants"""
        max_var = self.variants.aggregate(max=models.Max('price'))['max']
        return max_var if max_var is not None else float(self.discounted_price)

    def get_colors(self):
        color_attr = self.attributes.filter(attribute__attribute_type='color').select_related('option__attribute')
        return list(set([v.option for v in color_attr]))

    def get_sizes(self):
        size_attr = self.attributes.filter(
            attribute__name__in=['Size', 'RAM', 'Storage', 'Storage Capacity']
        ).select_related('option')
        return list(set([v.option for v in size_attr]))


class ProductVariant(models.Model):
    """Individual product variants (e.g., iPhone 14 128GB Blue)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='variants/', blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    attributes = models.ManyToManyField(
        AttributeOption,
        through='ProductVariantAttribute',
        related_name='variants'
    )

    def __str__(self):
        attrs = ', '.join([str(pa.attribute_option.value) for pa in self.attribute_values.all()])
        return f"{self.product.title} - {attrs}"

    def get_effective_price(self):
        return self.price if self.price is not None else self.product.discounted_price

    def get_effective_compare_price(self):
        return self.compare_price if self.compare_price is not None else self.product.selling_price

    def discount_percent(self):
        p = self.get_effective_price()
        cp = self.get_effective_compare_price()
        if cp > 0:
            return int((cp - p) / cp * 100)
        return 0

    def is_in_stock(self):
        return self.stock > 0


class ProductVariantAttribute(models.Model):
    """Links a variant to its attribute options"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    option = models.ForeignKey(AttributeOption, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['variant', 'attribute', 'option']

    def __str__(self):
        return f"{self.variant}: {self.option.value}"


class ProductSpecification(models.Model):
    """Key-value product specifications"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    spec_name = models.CharField(max_length=100)  # "Display", "Processor"
    spec_value = models.CharField(max_length=255)  # "6.7 inch AMOLED", "Snapdragon 8 Gen 2"
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'spec_name']

    def __str__(self):
        return f"{self.spec_name}: {self.spec_value}"


# ============================================================
# Recently Viewed
# ============================================================
class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-viewed_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} viewed {self.product.title}"


# ============================================================
# Wishlist
# ============================================================
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

    def item_count(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['wishlist', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.wishlist.user.username} - {self.product.title}"


# ============================================================
# Cart
# ============================================================
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_subtotal(self):
        return sum(item.get_total() for item in self.items.select_related('product', 'variant').all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def get_shipping(self):
        subtotal = float(self.get_subtotal())
        return 0.0 if subtotal >= 500 else 49.0

    def get_tax(self):
        return round(self.get_subtotal() * 0.05, 2)

    def get_grand_total(self):
        return self.get_subtotal() + self.get_shipping() + self.get_tax()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        var_str = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity} x {self.product.title}{var_str}"

    def get_unit_price(self):
        if self.variant and self.variant.price is not None:
            return self.variant.get_effective_price()
        return self.product.discounted_price

    def get_total(self):
        return float(self.get_unit_price()) * self.quantity


# ============================================================
# Payment
# ============================================================
class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('cod', 'Cash on Delivery'),
        ('emi', 'EMI'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_holder = models.CharField(max_length=100, blank=True)
    card_type = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{self.id.hex[:12].upper()}"
        super().save(*args, **kwargs)


# ============================================================
# Orders
# ============================================================
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(CartItem, related_name='order_items')
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=ORDER_STATUS, default='pending')
    order_number = models.CharField(max_length=20, unique=True)
    expected_delivery = models.DateField(null=True, blank=True)
    tracking_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    coupon_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{self.id.hex[:8].upper()}"
        super().save(*kwargs)

    def __str__(self):
        return f"Order {self.order_number}"

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def can_cancel(self):
        return self.status in ['pending', 'confirmed', 'processing']

    def can_return(self):
        return self.status == 'delivered'

    def get_status_progress(self):
        status_order = ['pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered']
        try:
            return status_order.index(self.status) / (len(status_order) - 1) * 100
        except ValueError:
            return 0


class OrderTracking(models.Model):
    """Individual tracking events for an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=30, choices=Order.ORDER_STATUS)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.order_number} - {self.title}"


class OrderItem(models.Model):
    """Denormalized order item for historical record"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product_title = models.CharField(max_length=200)
    product_brand = models.CharField(max_length=100, blank=True)
    variant_info = models.CharField(max_length=200, blank=True)
    product_image = models.ImageField(upload_to='order_items/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product_title} x {self.quantity}"


# ============================================================
# Returns
# ============================================================
class ReturnRequest(models.Model):
    RETURN_STATUS = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('pickup_scheduled', 'Pickup Scheduled'),
        ('picked_up', 'Picked Up'),
        ('refund_processing', 'Refund Processing'),
        ('refund_completed', 'Refund Completed'),
        ('rejected', 'Rejected'),
    ]
    REASON_CHOICES = [
        ('damaged', 'Product Damaged'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not as Described'),
        ('defective', 'Defective/Not Working'),
        ('changed_mind', 'Changed My Mind'),
        ('late_delivery', 'Delivery Too Late'),
        ('duplicate', 'Duplicate Order'),
        ('other', 'Other'),
    ]
    REFUND_METHOD = [
        ('original', 'Original Payment Method'),
        ('bank', 'Bank Account'),
        ('wallet', 'Wallet'),
        ('exchange', 'Gift Card/Store Credit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_detail = models.TextField(blank=True)
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD, default='original')
    bank_account = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=30, choices=RETURN_STATUS, default='requested')
    pickup_date = models.DateField(null=True, blank=True)
    pickup_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_reference = models.CharField(max_length=50, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return #{self.id.hex[:8].upper()} - {self.order.order_number}"


# ============================================================
# Coupons
# ============================================================
class Coupon(models.Model):
    CODE_TYPE = [
        ('percent', 'Percentage Off'),
        ('flat', 'Flat Discount'),
        ('bogo', 'Buy One Get One'),
        ('free_shipping', 'Free Shipping'),
    ]
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=CODE_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='coupons')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Coupons"

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

    def calculate_discount(self, cart_total):
        if not self.is_valid() or float(cart_total) < float(self.min_order_amount):
            return 0
        if self.discount_type == 'percent':
            disc = float(cart_total) * float(self.discount_value) / 100
            return min(disc, float(self.max_discount)) if self.max_discount else disc
        elif self.discount_type == 'flat':
            return min(float(self.discount_value), float(cart_total))
        return 0


# ============================================================
# Reviews
# ============================================================
class Review(models.Model):
    VERIFICATION = [
        ('verified', 'Verified Purchase'),
        ('unverified', 'Unverified'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    verification_status = models.CharField(max_length=20, choices=VERIFICATION, default='unverified')
    helpful_count = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating
        all_reviews = Review.objects.filter(product=self.product)
        self.product.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
        self.product.num_reviews = len(all_reviews)
        self.product.save(update_fields=['rating', 'num_reviews'])


class ReviewHelpful(models.Model):
    """Track helpful votes on reviews"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'review']
