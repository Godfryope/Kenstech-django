from django.views.generic import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import *

class ProductListView(ListView):
    model = Product
    template_name = 'store/index.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     title = self.request.GET.get('title')
    #     if title:
    #         queryset = queryset.filter(name__icontains=title)
    #     return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['cart_items'] = self.get_cart_items()
        # context['wishlist_items'] = self.get_wishlist_items()
        context['hot_deals'] = self.get_hot_deals()
        context['newitems'] = self.get_new_items()
        context['top_selling'] = self.get_top_selling()
        context['search_query'] = self.request.GET.get('title', '')
        return context

    # def get_cart_items(self):
    #     # Logic to retrieve and return the items in the cart for the current user
    #     cart = self.request.session.get('cart', {})
    #     cart_items = []
    #     for slug, item_data in cart.items():
    #         product = get_object_or_404(Product, slug=slug)
    #         cart_items.append({
    #             'product': product,
    #             'quantity': item_data.get('quantity', 0),
    #             'variable_features': item_data.get('variable_features', {}),
    #         })
    #     return cart_items

    def get_new_items(self):
        # Logic to retrieve and return the items in the items that are new for the current user
        newitems = Product.objects.filter(hot_deal=True)
        return newitems

    def get_hot_deals(self):
        # Logic to retrieve and return the hot deal products
        hot_deals = Product.objects.filter(hot_deal=True)
        return hot_deals

    def get_top_selling(self):
        # Logic to retrieve and return the top selling products
        top_selling = Product.objects.order_by('-sales')[:5]
        return top_selling


# from django.core.serializers import serialize

class ProductDetailView(TemplateView):
    model = Product
    context_object_name = 'product'
    template_name = 'store/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        # quantity = CartItem.objects.filter(quantity)
        context['product'] = product
         # Retrieve the quantity from the cart if the item exists
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user).first()
            if cart:
                cart_item = cart.items.filter(product=product).first()
                if cart_item:
                    context['quantity'] = cart_item.quantity

        return context

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        quantity = int(request.POST.get('quantity', 1))

        # Get or create the user's cart
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)

        # Check if the item is already in the cart
        cart_item, item_created = CartItem.objects.get_or_create(user=user, product=product)

        # Update the quantity if the item already exists in the cart
        if not item_created:
            cart_item.quantity = quantity
            cart_item.save()

        # Add the item to the cart if it's a new item
        else:
            cart_item.quantity = quantity
            cart_item.save()
            cart.items.add(cart_item)

        return redirect('cart')



class CartPageView(TemplateView):
    template_name = 'store/cart.html'

    def get_cart(self):
        # Retrieve the cart object based on user or session
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart = get_object_or_404(Cart, user=self.request.user)
        else:
            # If the user is anonymous, retrieve the cart from the session
            product_slug = self.request.session.get('product_slug')
            cart = get_object_or_404(Cart, id=product_slug)

        return cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        cart_items = CartItem.objects.filter(cart=cart)
        context['cart_items'] = cart_items
        context['total_price'] = cart.get_total_price()
        return context

