from django.urls import path
from .views import *

urlpatterns = [
    # Product List View
    path('', ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartPageView.as_view(), name='cart'),
    # path('checkout/', CheckoutPageView.as_view(), name='checkout'),
    # path('add-to-cart/<slug:product_slug>/', AddToCartView.as_view(), name='add-to-cart'),

    # # Cart View
    # path('cart/', CartView.as_view(), name='cart'),

    # # Wishlist View
    # path('wishlist/', WishlistView.as_view(), name='wishlist'),
]
