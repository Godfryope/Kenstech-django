from django.urls import path
from .views import *
from django.contrib.auth.views import *

urlpatterns = [
    # Product List View
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartPageView.as_view(), name='cart'),
    # path('profile/settings/', ProfileSettingsView.as_view(), name='profile_settings'),
]
