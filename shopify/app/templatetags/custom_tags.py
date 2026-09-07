from django import template
from app.models import Wishlist, Cart, CartItem

register = template.Library()


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def in_wishlist(product, request):
    """Check if a product is in the user's wishlist"""
    if not request.session.get('is_log_in'):
        return False
    try:
        from app.models import User
        user = User.objects.get(username=request.session['user'])
        wishlist = Wishlist.objects.filter(user=user).first()
        if not wishlist:
            return False
        return wishlist.items.filter(product=product).exists()
    except Exception:
        return False


@register.filter
def add_days(value, days):
    from datetime import timedelta
    try:
        return (value + timedelta(days=int(days))).strftime('%b %d')
    except Exception:
        return value


@register.filter
def cart_count(request):
    """Return number of items in user's cart"""
    if not request.session.get('is_log_in'):
        return 0
    try:
        from app.models import User
        user = User.objects.get(username=request.session['user'])
        cart = Cart.objects.filter(user=user).first()
        return cart.get_item_count() if cart else 0
    except Exception:
        return 0


@register.filter
def wishlist_count(request):
    """Return number of items in user's wishlist"""
    if not request.session.get('is_log_in'):
        return 0
    try:
        from app.models import User
        user = User.objects.get(username=request.session['user'])
        wishlist = Wishlist.objects.filter(user=user).first()
        return wishlist.item_count() if wishlist else 0
    except Exception:
        return 0


@register.simple_tag
def in_cart(user, product):
    """Check if a product is in user's cart"""
    if not user or user.is_anonymous:
        return 0
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return 0
    item = cart.items.filter(product=product).first()
    return item.quantity if item else 0
