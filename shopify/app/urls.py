from django.urls import path
from . import views

urlpatterns = [
    # Static
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Address
    path('add_address/', views.add_address, name='add_address'),
    path('show_add/', views.read_address, name='show_add'),
    path('update_add/<int:pk>/', views.update_add, name='update_add'),
    path('delete_add/<int:pk>/', views.delete_add, name='delete_add'),

    # Products
    path('add_product/', views.add_product, name='add_product'),
    path('show_prod/', views.show_product, name='show_prod'),
    path('pro_detail/<int:pk>/', views.product_detail, name='pro_detail'),
    path('category/<slug:slug>/', views.products_by_category, name='products_by_category'),
    path('compare/', views.compare_view, name='compare'),
    path('compare/add/<int:product_id>/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/<int:product_id>/', views.remove_from_compare, name='remove_from_compare'),

    # Product AJAX APIs
    path('api/variant-price/<int:product_id>/', views.get_variant_price, name='variant_price'),
    path('api/wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('api/wishlist/count/', views.get_wishlist_count, name='wishlist_count'),

    # Reviews
    path('product/<int:pk>/review/', views.add_review, name='add_review'),
    path('review/helpful/', views.mark_review_helpful, name='mark_review_helpful'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),

    # Cart
    path('add_to_cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('show_cart/', views.cart_view, name='show_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Checkout
    path('place_order/', views.place_order, name='place_order'),

    # Payment
    path('payment/<uuid:order_id>/', views.payment_view, name='payment'),
    path('process_payment/<uuid:order_id>/', views.process_payment, name='process_payment'),
    path('receipt/<uuid:order_id>/', views.receipt, name='receipt'),

    # Orders
    path('show_order/', views.show_order, name='show_order'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('order/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<uuid:order_id>/return/', views.return_order, name='return_order'),
    path('return/<uuid:return_id>/', views.return_detail, name='return_detail'),
]
