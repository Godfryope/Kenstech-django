from django.views.generic import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from .models import *
from .forms import *

class ProductListView(ListView):
    model = Product
    template_name = 'store/index.html'
    context_object_name = 'products'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # If the user is not authenticated, redirect to the login page
            return redirect(reverse('account_login'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset.annotate(sales_count=Coalesce(Count('cartitem'), 0)).order_by('-sales')
    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     title = self.request.GET.get('title')
    #     if title:
    #         queryset = queryset.filter(name__icontains=title)
    #     return queryset

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve the top selling products based on the count of times added to cart
        top_selling = self.get_queryset()[:3]

        # Retrieve the cart items count for the current user
        cart = self.get_cart()
        context['cart_items_count'] = cart.get_total_items() if cart else 0
        context['top_selling'] = top_selling
        context['wishlist_items_count'] = self.wishlist_items_count()
        context['hot_deals'] = self.get_hot_deals()
        context['newitems'] = self.get_new_items()
        context['search_query'] = self.request.GET.get('title', '')
    
        return context
    
    def get_cart(self):
        # Retrieve the cart object based on user or session
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
        else:
            # If the user is anonymous, retrieve the cart from the session
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = get_object_or_404(Cart, id=cart_id)
            else:
                cart = Cart.objects.create()
                self.request.session['cart_id'] = cart.id

        return cart
    
    def post(self, request, *args, **kwargs):
        newsletter_form = NewsletterSubscriberForm(request.POST)
        if newsletter_form.is_valid():
            newsletter_form.save()
            messages.success(request, 'Successfully subscribed to the newsletter!')
        else:
            messages.error(request, 'Failed to subscribe to the newsletter.')

        return self.get(request, *args, **kwargs)
    
    def wishlist_items_count(self):
        # Logic to retrieve and return the count of items in the wishlist for the current user
        wishlist_items_count = 0
        user = self.request.user
        if user.is_authenticated:
            wishlist_items_count = WishlistItem.objects.filter(wishlist__user=user).count()
        return wishlist_items_count

    

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
    template_name = 'store/product.html'
    related_products_per_page = 4

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        # quantity = CartItem.objects.filter(quantity)


        # Retrieve the cart items count for the current user
        cart = self.get_cart()
        context['cart_items_count'] = cart.get_total_items() if cart else 0
        context['product'] = product
        context['wishlist_items_count'] = self.wishlist_items_count()
        related_products = self.get_related_products(product)
        paginator = Paginator(related_products, self.related_products_per_page)
        page_number = self.request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        context['related_products'] = page
         # Retrieve the quantity from the cart if the item exists
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user).first()
            if cart:
                cart_item = cart.items.filter(product=product).first()
                if cart_item:
                    context['quantity'] = cart_item.quantity
                else:
                    context['quantity'] = 0
            else:
                context['quantity'] = 0
        else:
            context['quantity'] = 0

        return context
    
    def get_related_products(self, product):
        # Get related products from the same category
        related_products = Product.objects.filter(categories__in=product.categories.all()).exclude(slug=product.slug)
        related_products = related_products.order_by('-timestamp')
        return related_products
    
    def wishlist_items_count(self):
        # Logic to retrieve and return the count of items in the wishlist for the current user
        wishlist_items_count = 0
        user = self.request.user
        if user.is_authenticated:
            wishlist_items_count = WishlistItem.objects.filter(wishlist__user=user).count()
        return wishlist_items_count


    def get_cart(self):
        # Retrieve the cart object based on user or session
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
        else:
            # If the user is anonymous, retrieve the cart from the session
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = get_object_or_404(Cart, id=cart_id)
            else:
                cart = Cart.objects.create()
                self.request.session['cart_id'] = cart.id

        return cart
        
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        quantity = int(request.POST.get('quantity', 1))

        user = self.request.user
        if user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
        else:
            cart, _ = Cart.objects.get_or_create()

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
            # Display a success message for adding the item to the cart
            messages.success(request, "Item added to cart successfully.")

        

        # Subscribe to the newsletter
        newsletter_form = NewsletterSubscriberForm(request.POST)
        if newsletter_form.is_valid():
            newsletter_form.save()
            # Display a success message for subscribing to the newsletter
            messages.success(request, "Successfully subscribed to the newsletter.")

        # Include the newsletter form in the context
        context['subscribetonewsletter'] = newsletter_form

        return self.render_to_response(context)



class CartPageView(TemplateView):
    template_name = 'store/cart.html'

    def get_cart(self):
        # Retrieve the cart object based on user or session
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
        else:
            # If the user is anonymous, retrieve the cart from the session
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = get_object_or_404(Cart, id=cart_id)
            else:
                cart = Cart.objects.create()
                self.request.session['cart_id'] = cart.id

        return cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        cart_items = CartItem.objects.filter(cart=cart)
        context['cart_items'] = cart_items
        context['total_price'] = cart.get_total_price()
        return context
    
# class SignupView(TemplateView):
#     template_name = 'store/signup.html'

