import re
from django import forms
from django.core.validators import RegexValidator
from .models import (
    User, Address, Product, ProductVariant, AttributeOption,
    Review, CartItem, Coupon, ReturnRequest
)


# ============================================================
# Authentication
# ============================================================
class UserForm(forms.ModelForm):
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        data = super().clean()
        pwd = data.get('password')
        confirm = data.get('confirm_password')

        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError('Passwords do not match.')

        if User.objects.filter(username=data.get('username')).exists():
            raise forms.ValidationError('Username already taken.')

        if User.objects.filter(email=data.get('email')).exists():
            raise forms.ValidationError('Email already registered.')

        return data


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )

    def clean(self):
        data = super().clean()
        username = data.get('username')
        password = data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)

                if not user.check_password(password):
                    raise forms.ValidationError(
                        'Invalid username or password.'
                    )

                if not user.is_active:
                    raise forms.ValidationError(
                        'This account is inactive.'
                    )

                data['user'] = user

            except User.DoesNotExist:
                raise forms.ValidationError(
                    'Invalid username or password.'
                )

        return data


# ============================================================
# Address
# ============================================================
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['user']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Full Name',
                'class': 'form-control'
            }),
            'locality': forms.TextInput(attrs={
                'placeholder': 'Street, Building',
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'City',
                'class': 'form-control'
            }),
            'pincode': forms.NumberInput(attrs={
                'placeholder': '6-digit PIN',
                'class': 'form-control'
            }),
            'state': forms.TextInput(attrs={
                'placeholder': 'State',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Mobile',
                'class': 'form-control'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'address_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


# ============================================================
# Product Filter
# ============================================================
class ProductFilterForm(forms.Form):
    """Search/filter form for the product listing page"""

    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('newest', 'Newest First'),
        ('rating', 'Customer Rating'),
        ('popularity', 'Most Popular'),
        ('discount', 'Best Discount'),
    ]

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search products...',
            'class': 'form-control'
        })
    )

    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Categories'
    )

    brand = forms.CharField(required=False)

    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min',
            'class': 'form-control'
        })
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max',
            'class': 'form-control'
        })
    )

    min_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'placeholder': '4+',
            'class': 'form-control'
        })
    )

    in_stock_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    free_delivery = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def __init__(self, *args, **kwargs):
        from .models import Category

        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        )


# ============================================================
# Product Creation
# ============================================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'title',
            'category',
            'brand',
            'description',
            'selling_price',
            'discounted_price',
            'unit',
            'stock',
            'product_image',
            'return_days',
            'tags',
            'is_featured',
            'is_bestseller',
            'is_new',
            'free_delivery',
            'cash_on_delivery',
        ]


# ============================================================
# Cart
# ============================================================
class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1
        })
    )

    variant_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )


class UpdateCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )


class CouponForm(forms.Form):
    code = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter coupon code',
            'class': 'form-control'
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code'].upper()

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise forms.ValidationError('Invalid coupon code.')

        if not coupon.is_valid():
            raise forms.ValidationError('This coupon has expired.')

        return code


# ============================================================
# Checkout
# ============================================================
class OrderForm(forms.Form):
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        empty_label="Select Address"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if user:
            self.fields['address'].queryset = Address.objects.filter(
                user=user
            )


# ============================================================
# Payment
# ============================================================
class CardPaymentForm(forms.Form):
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'placeholder': '1234 5678 9012 3456',
            'maxlength': '19',
            'class': 'form-control card-number-input',
            'autocomplete': 'cc-number',
        })
    )

    card_holder = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Name on Card',
            'class': 'form-control'
        })
    )

    expiry_date = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'placeholder': 'MM/YYYY',
            'class': 'form-control',
            'maxlength': '7'
        })
    )

    cvv = forms.CharField(
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'CVV',
            'class': 'form-control',
            'maxlength': '4'
        })
    )

    def clean_card_number(self):
        cn = self.cleaned_data.get(
            'card_number',
            ''
        ).replace(' ', '').replace('-', '')

        if not cn.isdigit() or not (13 <= len(cn) <= 19):
            raise forms.ValidationError('Invalid card number.')

        return cn

    def clean_expiry_date(self):
        expiry = self.cleaned_data.get(
            'expiry_date',
            ''
        ).strip()

        if not re.match(r'^\d{2}/\d{4}$', expiry):
            raise forms.ValidationError('Use format MM/YYYY.')

        month, year = expiry.split('/')

        if not (1 <= int(month) <= 12):
            raise forms.ValidationError('Invalid month.')

        return expiry


class UPIForm(forms.Form):
    upi_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'yourname@bank',
            'class': 'form-control'
        }),
        help_text='Example: yourname@upi'
    )

    def clean_upi_id(self):
        upi = self.cleaned_data.get(
            'upi_id',
            ''
        ).strip()

        if '@' not in upi or len(upi) < 5:
            raise forms.ValidationError(
                'Please enter a valid UPI ID.'
            )

        return upi


class NetbankingForm(forms.Form):
    BANK_CHOICES = [
        ('', 'Select Bank'),
        ('sbi', 'State Bank of India'),
        ('hdfc', 'HDFC Bank'),
        ('icici', 'ICICI Bank'),
        ('axis', 'Axis Bank'),
        ('kotak', 'Kotak Mahindra Bank'),
        ('pnb', 'Punjab National Bank'),
        ('bob', 'Bank of Baroda'),
        ('canara', 'Canara Bank'),
        ('idfc', 'IDFC FIRST Bank'),
        ('yes', 'Yes Bank'),
        ('other', 'Other Banks'),
    ]

    bank = forms.ChoiceField(
        choices=BANK_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class WalletForm(forms.Form):
    WALLET_CHOICES = [
        ('', 'Select Wallet'),
        ('paytm', 'Paytm Wallet'),
        ('phonepe', 'PhonePe'),
        ('gpay', 'Google Pay'),
        ('amazon', 'Amazon Pay'),
        ('mobikwik', 'MobiKwik'),
    ]

    wallet = forms.ChoiceField(
        choices=WALLET_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    mobile = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'Registered mobile',
            'class': 'form-control'
        })
    )

    def clean_mobile(self):
        m = self.cleaned_data.get(
            'mobile',
            ''
        ).strip()

        if not m.isdigit() or len(m) != 10:
            raise forms.ValidationError(
                'Enter a valid 10-digit mobile number.'
            )

        return m


# ============================================================
# Reviews
# ============================================================
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Summarize your review',
                'class': 'form-control'
            }),
            'comment': forms.Textarea(attrs={
                'placeholder': 'Share your experience...',
                'rows': 4,
                'class': 'form-control'
            }),
        }


class ReviewHelpfulForm(forms.Form):
    review_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )


# ============================================================
# Returns
# ============================================================
class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = [
            'reason',
            'reason_detail',
            'refund_method',
            'bank_account'
        ]

        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reason_detail': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Provide more details...'
            }),
            'refund_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'For refund via bank account'
            }),
        }


# ============================================================
# Profile
# ============================================================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }