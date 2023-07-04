from django.urls import path
from .views import *
from django.contrib.auth.views import *

urlpatterns = [
    # Product List View
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartPageView.as_view(), name='cart'),
    # path('accounts/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    # path('accounts/password/reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('accounts/login/', LoginView.as_view(), name='login'),
    # path('accounts/signup/', SignUpView.as_view(), name='signup'),
    # path('checkout/', CheckoutPageView.as_view(), name='checkout'),
    # path('add-to-cart/<slug:product_slug>/', AddToCartView.as_view(), name='add-to-cart'),

    # # Cart View
    # path('cart/', CartView.as_view(), name='cart'),

    # # Wishlist View
    # path('wishlist/', WishlistView.as_view(), name='wishlist'),
]
