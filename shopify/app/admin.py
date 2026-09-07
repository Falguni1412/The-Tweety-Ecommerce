from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['username', 'email']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'city', 'state', 'pincode', 'is_default']
    list_filter = ['state', 'is_default']
    search_fields = ['name', 'locality', 'city', 'pincode']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_order', 'is_active', 'get_product_count']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['display_order', 'is_active']


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'attribute_type', 'display_order']
    list_editable = ['attribute_type', 'display_order']


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'slug', 'color_code', 'display_order']
    list_filter = ['attribute']
    prepopulated_fields = {'slug': ('value',)}


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class SpecInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'discounted_price', 'stock', 'rating', 'is_featured', 'is_active']
    list_filter = ['category', 'brand', 'is_featured', 'is_bestseller', 'is_new', 'is_active']
    search_fields = ['title', 'brand', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['discounted_price', 'stock', 'is_featured', 'is_active']
    inlines = [VariantInline, SpecInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'price', 'stock', 'is_active']
    list_filter = ['is_active', 'product__category']
    search_fields = ['sku', 'product__title']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'item_count']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username']
    readonly_fields = ['order_number', 'id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'order', 'payment_type', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_type', 'created_at']
    search_fields = ['transaction_id', 'user__username']


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'reason', 'status', 'refund_amount', 'created_at']
    list_filter = ['status', 'reason', 'created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'discount_type', 'discount_value', 'min_order_amount', 'valid_until', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'title']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'verification_status', 'created_at']
    list_filter = ['rating', 'verification_status', 'created_at']
