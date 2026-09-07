import random, string, json
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Min, Max, Count, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse

from .models import (
    User, Address, Category, Product, ProductVariant, ProductSpecification,
    ProductAttribute, AttributeOption, RecentlyViewed, Wishlist, WishlistItem,
    Cart, CartItem, Order, OrderItem, OrderTracking, Payment,
    ReturnRequest, Coupon, Review
)
from .forms import (
    UserForm, LoginForm, AddressForm, ProductForm, ProductFilterForm,
    AddToCartForm, UpdateCartForm, CouponForm, OrderForm,
    CardPaymentForm, UPIForm, NetbankingForm, WalletForm,
    ReviewForm, ReturnRequestForm, ProfileForm
)


# ============================================================
# Helpers
# ============================================================
def get_user(request):
    if not request.session.get('is_log_in'):
        return None
    try:
        return User.objects.get(username=request.session['user'])
    except User.DoesNotExist:
        return None


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ============================================================
# Authentication
# ============================================================
def register_view(request):
    if request.session.get('is_log_in'):
        return redirect('app:home')
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, 'Account created! Please log in.')
            return redirect('app:login')
    else:
        form = UserForm()
    return render(request, 'user/register.html', {'form': form})


def login_view(request):
    if request.session.get('is_log_in'):
        return redirect('app:home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            request.session['user'] = form.cleaned_data['username']
            request.session['is_log_in'] = True
            messages.success(request, 'Welcome back!')
            return redirect('app:home')
    else:
        form = LoginForm()
    return render(request, 'user/login.html', {'form': form})


def logout_view(request):
    request.session['is_log_in'] = False
    if 'user' in request.session:
        del request.session['user']
    messages.info(request, 'Logged out successfully.')
    return redirect('app:home')


def profile_view(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    addresses = user.addresses.all()
    orders = user.orders.all().order_by('-created_at')[:5]
    wishlist_count = Wishlist.objects.filter(user=user).first()
    return render(request, 'user/profile.html', {
        'user': user,
        'addresses': addresses,
        'orders': orders,
        'wishlist_count': wishlist_count.item_count() if wishlist_count else 0,
        'total_orders': user.orders.count(),
    })


def profile_edit(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('app:profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'user/profile_edit.html', {'form': form})


# ============================================================
# Home Page
# ============================================================
def home(request):
    user = get_user(request)
    featured = Product.objects.filter(is_active=True, is_featured=True)[:8]
    bestsellers = Product.objects.filter(is_active=True, is_bestseller=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new=True).order_by('-created_at')[:8]
    deals = Product.objects.filter(
        is_active=True
    ).exclude(discounted_price=0).order_by('?')[:6]
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    )

    # Personalized: recently viewed
    recently_viewed = []
    if user:
        recently_viewed = list(
            RecentlyViewed.objects.filter(user=user)
            .select_related('product')
            .values_list('product_id', flat=True)[:8]
        )
        recently_viewed = list(Product.objects.filter(id__in=recently_viewed, is_active=True)[:8])

    # Top rated
    top_rated = Product.objects.filter(
        is_active=True, num_reviews__gt=0
    ).order_by('-rating', '-num_reviews')[:8]

    return render(request, 'home.html', {
        'featured': featured,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'deals': deals,
        'categories': categories,
        'recently_viewed': recently_viewed,
        'top_rated': top_rated,
    })


# ============================================================
# Products - Listing with Search & Filters
# ============================================================
def show_product(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.filter(is_active=True)

    # Build filter from query params
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    brand = request.GET.get('brand', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')
    in_stock = request.GET.get('in_stock')
    free_delivery = request.GET.get('free_delivery')
    sort = request.GET.get('sort', 'relevance')
    page = request.GET.get('page', 1)

    if q:
        products = products.filter(
            Q(title__icontains=q) | Q(brand__icontains=q) |
            Q(description__icontains=q) | Q(tags__contains=[q])
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if brand:
        products = products.filter(brand__icontains=brand)

    if min_price:
        products = products.filter(discounted_price__gte=min_price)
    if max_price:
        products = products.filter(discounted_price__lte=max_price)

    if min_rating:
        products = products.filter(rating__gte=min_rating)

    if in_stock:
        products = products.filter(stock__gt=0)

    if free_delivery:
        products = products.filter(free_delivery=True)

    # Sorting
    sort_map = {
        'price_low': 'discounted_price',
        'price_high': '-discounted_price',
        'newest': '-created_at',
        'rating': '-rating',
        'popularity': '-num_sold',
        'discount': '-selling_price',
    }
    if sort in sort_map:
        products = products.order_by(sort_map[sort])

    # Get filter for sidebar
    brands = Product.objects.filter(
        is_active=True, category__slug=category_slug
    ).values_list('brand', flat=True).distinct() if category_slug else \
        Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct()

    # Pagination
    paginator = Paginator(products, 20)
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # Price range
    price_range = Product.objects.filter(is_active=True).aggregate(
        min=Min('discounted_price'), max=Max('discounted_price')
    )

    return render(request, 'product/show.html', {
        'products': products_page,
        'categories': categories,
        'brands': sorted(set(b.strip() for b in brands if b)),
        'price_range': price_range,
        'filter': {
            'q': q, 'category': category_slug, 'brand': brand,
            'min_price': min_price, 'max_price': max_price,
            'min_rating': min_rating, 'in_stock': in_stock,
            'free_delivery': free_delivery, 'sort': sort,
        },
    })


def products_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    categories = Category.objects.filter(is_active=True)
    return render(request, 'product/show.html', {
        'products': products,
        'categories': categories,
        'current_category': category,
    })


# ============================================================
# Product Detail
# ============================================================
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related(
        'variants__attribute_values__option',
        'specifications',
        'variants__attribute_values__attribute'
    ), pk=pk, is_active=True)

    # Track recently viewed
    user = get_user(request)
    if user:
        RecentlyViewed.objects.update_or_create(
            user=user, product=product,
            defaults={'viewed_at': timezone.now()}
        )

    reviews = product.reviews.all().order_by('-created_at')
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=pk)[:8]
    review_form = ReviewForm() if user else None

    # Specs as dict
    specs = {s.spec_name: s.spec_value for s in product.specifications.all()}

    # Attributes for variant selection
    variant_attrs = {}
    for v in product.variants.filter(is_active=True):
        for av in v.attribute_values.select_related('option', 'attribute').all():
            attr_name = av.attribute.name
            if attr_name not in variant_attrs:
                variant_attrs[attr_name] = []
            variant_attrs[attr_name].append({
                'option_id': av.option.id,
                'option_value': av.option.value,
                'color_code': av.option.color_code,
                'variant_id': v.id,
                'price': str(v.price) if v.price else str(product.discounted_price),
                'stock': v.stock,
            })
            # deduplicate
            seen = set()
            variant_attrs[attr_name] = [
                x for x in variant_attrs[attr_name]
                if x['option_id'] not in seen and not seen.add(x['option_id'])
            ]

    return render(request, 'product/product_detail.html', {
        'product': product,
        'reviews': reviews[:5],
        'all_reviews': reviews,
        'related': related,
        'review_form': review_form,
        'specs': specs,
        'variant_attrs': variant_attrs,
        'user': user,
    })


@require_POST
def add_review(request, pk):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    product = get_object_or_404(Product, pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = user
        review.product = product
        # Check if verified purchase
        if Order.objects.filter(user=user, order_items__product_title=product.title).exists():
            review.verification_status = 'verified'
        review.save()
        messages.success(request, 'Review submitted!')
    return redirect('app:pro_detail', pk=pk)


@require_POST
def mark_review_helpful(request):
    if not request.session.get('is_log_in'):
        return JsonResponse({'error': 'Login required'}, status=401)
    from .models import ReviewHelpful
    user = get_user(request)
    review_id = request.POST.get('review_id')
    is_helpful = request.POST.get('is_helpful') == 'true'
    review = get_object_or_404(Review, pk=review_id)
    obj, created = ReviewHelpful.objects.update_or_create(
        user=user, review=review,
        defaults={'is_helpful': is_helpful}
    )
    if not created and obj.is_helpful == is_helpful:
        obj.delete()  # toggle off
    count = review.helpful_votes.filter(is_helpful=True).count()
    return JsonResponse({'helpful_count': count})


# ============================================================
# Variant Price API
# ============================================================
def get_variant_price(request, product_id):
    variant_id = request.GET.get('variant_id')
    product = get_object_or_404(Product, pk=product_id)
    if variant_id:
        try:
            variant = ProductVariant.objects.get(pk=variant_id, product=product)
            return JsonResponse({
                'price': str(variant.get_effective_price()),
                'compare_price': str(variant.get_effective_compare_price()),
                'stock': variant.stock,
                'discount': variant.discount_percent(),
                'in_stock': variant.is_in_stock(),
            })
        except ProductVariant.DoesNotExist:
            pass
    return JsonResponse({
        'price': str(product.discounted_price),
        'compare_price': str(product.selling_price),
        'stock': product.stock,
        'discount': product.discount_percent(),
        'in_stock': not product.is_out_of_stock(),
    })


# ============================================================
# Wishlist
# ============================================================
def wishlist_view(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    items = wishlist.items.select_related('product').all()
    return render(request, 'product/wishlist.html', {'wishlist': wishlist, 'items': items})


@require_POST
def toggle_wishlist(request, product_id):
    if not request.session.get('is_log_in'):
        return JsonResponse({'error': 'Login required', 'redirect': '/login/'}, status=401)
    user = get_user(request)
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    if not created:
        item.delete()
    return JsonResponse({
        'in_wishlist': created is False,
        'count': wishlist.item_count()
    })


def get_wishlist_count(request):
    user = get_user(request)
    if not user:
        return JsonResponse({'count': 0})
    wishlist = Wishlist.objects.filter(user=user).first()
    return JsonResponse({'count': wishlist.item_count() if wishlist else 0})


# ============================================================
# Cart
# ============================================================
def add_to_cart(request, pk):
    user = get_user(request)
    if not user:
        messages.warning(request, 'Please log in to add items to cart.')
        return redirect('app:login')
    product = get_object_or_404(Product, pk=pk)
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(pk=variant_id, product=product)
            if variant.stock < quantity:
                messages.error(request, f'Only {variant.stock} units available.')
                return redirect('app:pro_detail', pk=pk)
        except ProductVariant.DoesNotExist:
            pass
    else:
        if product.stock < quantity:
            messages.error(request, f'Only {product.stock} units in stock.')
            return redirect('app:pro_detail', pk=pk)

    cart = get_or_create_cart(user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant,
        defaults={'quantity': quantity}
    )
    if not created:
        new_qty = cart_item.quantity + quantity
        max_stock = variant.stock if variant else product.stock
        if new_qty > max_stock:
            new_qty = max_stock
        cart_item.quantity = new_qty
        cart_item.save()

    messages.success(request, f'{product.title} added to cart!')
    return redirect('app:show_cart')


def update_cart(request, pk):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=user)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        if qty <= 0:
            cart_item.delete()
            messages.info(request, 'Item removed.')
        else:
            cart_item.quantity = qty
            cart_item.save()
            messages.success(request, 'Cart updated.')
    return redirect('app:show_cart')


def remove_from_cart(request, pk):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=user)
    cart_item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('app:show_cart')


def cart_view(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    cart = get_or_create_cart(user)
    subtotal = cart.get_subtotal()
    shipping = cart.get_shipping()
    tax = cart.get_tax()
    grand_total = cart.get_grand_total()
    coupon_form = CouponForm()
    applied_coupon = None
    discount = 0

    # Check for applied coupon
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            discount = coupon.calculate_discount(subtotal)
            applied_coupon = coupon
            grand_total = subtotal + shipping + tax - discount
        except Coupon.DoesNotExist:
            pass

    return render(request, 'product/show_cart.html', {
        'cart': cart,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'discount': discount,
        'grand_total': grand_total,
        'coupon_form': coupon_form,
        'applied_coupon': applied_coupon,
    })


@require_POST
def apply_coupon(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    form = CouponForm(request.POST)
    if form.is_valid():
        coupon = Coupon.objects.get(code=form.cleaned_data['code'])
        request.session['coupon_code'] = coupon.code
        messages.success(request, f'Coupon "{coupon.code}" applied!')
    else:
        messages.error(request, form.errors['code'].as_text() if 'code' in form.errors else str(form.errors))
    return redirect('app:show_cart')


@require_POST
def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.info(request, 'Coupon removed.')
    return redirect('app:show_cart')


# ============================================================
# Checkout
# ============================================================
@require_http_methods(["GET", "POST"])
def place_order(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    cart = get_or_create_cart(user)
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty!')
        return redirect('app:show_cart')

    addresses = Address.objects.filter(user=user)
    if not addresses.exists():
        messages.warning(request, 'Please add a delivery address first.')
        return redirect('app:add_address')

    subtotal = cart.get_subtotal()
    shipping = cart.get_shipping()
    tax = cart.get_tax()
    discount = 0
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            discount = coupon.calculate_discount(subtotal)
        except Coupon.DoesNotExist:
            discount = 0
    grand_total = subtotal + shipping + tax - discount

    if request.method == 'POST':
        address_id = request.POST.get('address')
        if not address_id:
            messages.error(request, 'Please select a delivery address.')
            return redirect('app:place_order')
        address = get_object_or_404(Address, id=address_id, user=user)

        order = Order.objects.create(
            user=user,
            shipping_address=address,
            subtotal=subtotal,
            shipping_cost=shipping,
            tax_amount=tax,
            discount_amount=discount,
            total_price=grand_total,
            coupon_used=coupon_code or '',
            status='pending',
            expected_delivery=timezone.now().date() + timedelta(days=4),
        )
        for item in cart.items.select_related('product', 'variant').all():
            order.items.add(item)
            # Create denormalized order item
            OrderItem.objects.create(
                order=order,
                product_title=item.product.title,
                product_brand=item.product.brand,
                variant_info=str(item.variant) if item.variant else '',
                product_image=item.product.product_image,
                price=item.get_unit_price(),
                quantity=item.quantity,
                total=item.get_total(),
            )
            # Deduct stock
            if item.variant:
                item.variant.stock = max(0, item.variant.stock - item.quantity)
                item.variant.save()
            else:
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save()

        # Add tracking event
        OrderTracking.objects.create(
            order=order, status='pending',
            title='Order Placed',
            description='Your order has been confirmed.',
            is_completed=True,
        )

        # Clear cart and coupon
        cart.items.all().delete()
        if 'coupon_code' in request.session:
            del request.session['coupon_code']

        return redirect('app:payment', order_id=order.id)

    return render(request, 'product/place_order.html', {
        'cart': cart,
        'addresses': addresses,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'discount': discount,
        'grand_total': grand_total,
    })


# ============================================================
# Payment
# ============================================================
def payment_view(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    if hasattr(order, 'payment') and order.payment.status == 'completed':
        return redirect('app:receipt', order_id=order.id)
    return render(request, 'product/payment.html', {
        'order': order,
        'card_form': CardPaymentForm(),
        'upi_form': UPIForm(),
        'netbanking_form': NetbankingForm(),
        'wallet_form': WalletForm(),
    })


@require_POST
def process_payment(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    payment_type = request.POST.get('payment_type', 'card')

    payment = Payment.objects.create(
        user=user,
        order=order,
        payment_type=payment_type,
        amount=order.total_price,
        status='processing',
    )

    if payment_type == 'card':
        form = CardPaymentForm(request.POST)
        if not form.is_valid():
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Invalid card details.')
            return redirect('app:payment', order_id=order.id)
        card_number = form.cleaned_data['card_number']
        payment.card_holder = form.cleaned_data['card_holder']
        payment.card_last_four = card_number[-4:]
        if card_number.startswith('4'):
            payment.card_type = 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            payment.card_type = 'Mastercard'
        elif card_number.startswith(('34', '37')):
            payment.card_type = 'Amex'
        else:
            payment.card_type = 'Card'
    elif payment_type == 'upi':
        form = UPIForm(request.POST)
        if not form.is_valid():
            payment.status = 'failed'
            payment.save()
            messages.error(request, form.errors['upi_id'].as_text())
            return redirect('app:payment', order_id=order.id)
        payment.upi_id = form.cleaned_data['upi_id']
    elif payment_type == 'netbanking':
        bank = request.POST.get('bank', '')
        if not bank:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Please select a bank.')
            return redirect('app:payment', order_id=order.id)
        banks = dict(NetbankingForm.BANK_CHOICES)
        payment.bank_name = banks.get(bank, bank)
    elif payment_type == 'wallet':
        wallet = request.POST.get('wallet', '')
        if not wallet:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Please select a wallet.')
            return redirect('app:payment', order_id=order.id)
        wallets = dict(WalletForm.WALLET_CHOICES)
        payment.bank_name = wallets.get(wallet, wallet)
    elif payment_type == 'cod':
        pass  # COD is always successful

    # Simulate payment success
    payment.status = 'completed'
    payment.completed_at = timezone.now()
    payment.save()

    order.status = 'confirmed'
    order.confirmed_at = timezone.now()
    order.save()

    # Add confirmed tracking
    OrderTracking.objects.create(
        order=order, status='confirmed',
        title='Payment Confirmed',
        description=f'Payment of ₹{order.total_price} received via {payment.get_payment_type_display()}.',
        is_completed=True,
    )
    OrderTracking.objects.create(
        order=order, status='processing',
        title='Processing Order',
        description='Your order is being prepared for shipment.',
    )

    return redirect('app:receipt', order_id=order.id)


# ============================================================
# Receipt & Orders
# ============================================================
def receipt(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    if not hasattr(order, 'payment'):
        return redirect('app:payment', order_id=order.id)
    return render(request, 'product/receipt.html', {
        'order': order,
        'payment': order.payment,
    })


def order_detail(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    return render(request, 'product/order_detail.html', {
        'order': order,
        'tracking_events': order.tracking_events.all(),
    })


def show_order(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(user=user).order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'product/show_order.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.ORDER_STATUS,
    })


def cancel_order(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('app:show_order')

    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        if hasattr(order, 'payment') and order.payment.status == 'completed':
            order.payment.status = 'refunded'
            order.payment.save()
        OrderTracking.objects.create(
            order=order, status='cancelled',
            title='Order Cancelled',
            description='Your order has been cancelled and refund initiated.',
            is_completed=True,
        )
        messages.success(request, 'Order cancelled. Refund will be processed in 5-7 days.')
        return redirect('app:show_order')
    return render(request, 'product/cancel_order.html', {'order': order})


# ============================================================
# Return Requests
# ============================================================
@require_http_methods(["GET", "POST"])
def return_order(request, order_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    order = get_object_or_404(Order, id=order_id, user=user)
    if not order.can_return():
        messages.error(request, 'Returns are only available for delivered orders.')
        return redirect('app:order_detail', order_id=order.id)

    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.order = order
            ret.refund_amount = order.total_price
            ret.save()
            order.status = 'returned'
            order.save()
            messages.success(request, 'Return request submitted! We will contact you soon.')
            return redirect('app:show_order')
    else:
        form = ReturnRequestForm()

    return render(request, 'product/return_order.html', {
        'order': order,
        'form': form,
    })


def return_detail(request, return_id):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    ret = get_object_or_404(ReturnRequest, id=return_id, order__user=user)
    return render(request, 'product/return_detail.html', {'ret': ret})


# ============================================================
# Address Management
# ============================================================
def add_address(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            add = form.save(commit=False)
            add.user = user
            if not user.addresses.exists():
                add.is_default = True
            add.save()
            messages.success(request, 'Address added!')
            return redirect('app:show_add')
    else:
        form = AddressForm()
    return render(request, 'user/add.html', {'form': form})


def read_address(request):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    return render(request, 'user/read_add.html', {'addresses': user.addresses.all()})


def update_add(request, pk):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    address = get_object_or_404(Address, pk=pk, user=user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated!')
            return redirect('app:show_add')
    else:
        form = AddressForm(instance=address)
    return render(request, 'user/update.html', {'form': form})


def delete_add(request, pk):
    user = get_user(request)
    if not user:
        return redirect('app:login')
    address = get_object_or_404(Address, pk=pk, user=user)
    address.delete()
    messages.success(request, 'Address deleted.')
    return redirect('app:show_add')


# ============================================================
# Product Add (admin)
# ============================================================
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product added!')
            return redirect('app:show_prod')
    else:
        form = ProductForm()
    return render(request, 'product/add_product.html', {'form': form})


# ============================================================
# Compare
# ============================================================
def compare_view(request):
    ids = request.session.get('compare_ids', [])
    products = Product.objects.filter(pk__in=ids, is_active=True) if ids else []
    return render(request, 'product/compare.html', {'products': products})


def add_to_compare(request, product_id):
    ids = request.session.get('compare_ids', [])
    if product_id not in ids and len(ids) < 4:
        ids.append(product_id)
        request.session['compare_ids'] = ids
        messages.success(request, 'Added to compare!')
    elif len(ids) >= 4:
        messages.warning(request, 'You can compare up to 4 products.')
    return redirect('app:pro_detail', pk=product_id)


def remove_from_compare(request, product_id):
    ids = request.session.get('compare_ids', [])
    if product_id in ids:
        ids.remove(product_id)
        request.session['compare_ids'] = ids
    return redirect('app:compare')


# ============================================================
# Static Pages
# ============================================================
def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')
