from django.views.generic import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .forms import *



class ProductListView(ListView):
    model = Product
    template_name = 'store/index.html'
    context_object_name = 'products'
    paginate_by = 20

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.is_authenticated:
    #         # If the user is not authenticated, redirect to the login page
    #         return redirect(reverse('account_login'))
    #     return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            if not queryset.exists():
                messages.success(self.request, "No item found")

        sort_option = self.request.GET.get('sort')
        if sort_option == 'popular':
            queryset = queryset.order_by('-sales')
        elif sort_option == 'position':
            queryset = queryset.order_by('timestamp')

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
        # top_selling = self.get_queryset()[:3]

        recent_products = Product.objects.order_by('-timestamp')[:3]
        new_products = Product.objects.filter(is_new=True)[:3]
        top_selling = Product.objects.order_by('-sales')[:3]
        context['recent_products'] = recent_products
        context['new_products'] = new_products

        # Retrieve the cart items count for the current user
        cart = self.get_cart()
        context['cart_items_count'] = cart.get_total_items() if cart else 0
        context['top_selling'] = top_selling
        context['wishlist_items_count'] = self.wishlist_items_count()
        context['hot_deals'] = self.get_hot_deals()
        context['newitems'] = self.get_new_items()
        context['search_query'] = self.request.GET.get('title', '')
        context['sort_option'] = self.request.GET.get('sort')
        context['show_option'] = self.request.GET.get('show')
        
    
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
        # Handling the "Add to Cart" form submission
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)

        user = self.request.user
        cart = self.get_cart()

        # Check if the item is already in the cart
        if user.is_authenticated:
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, user=user, product=product)
        else:
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

        # Update the quantity if the item already exists in the cart
        if not item_created:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Item added to cart successfully.")
        else:
            # Add the item to the cart if it's a new item
            cart_item.quantity = quantity
            cart_item.save()
            if cart:
                cart.items.add(cart_item)
            messages.success(request, "Item added to cart successfully.")

        # Store the quantity in the session
        cart_id = cart.id
        request.session[f'cart_{cart_id}_quantity'] = quantity

        # Subscribe to the newsletter
        newsletter_form = NewsletterSubscriberForm(request.POST)
        if newsletter_form.is_valid():
            newsletter_form.save()
            messages.success(request, "Successfully subscribed to the newsletter.")

        return redirect('product_list')
    
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
        cart = Cart.objects.filter(user=self.request.user).first() if self.request.user.is_authenticated else self.get_cart()
        if cart:
            cart_item = cart.items.filter(product=product).first()
            if cart_item:
                context['quantity'] = cart_item.quantity
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
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart = Cart.objects.filter(user=self.request.user).first()
        else:
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.filter(id=cart_id).first()
            else:
                cart = Cart.objects.create()
                self.request.session['cart_id'] = cart.id
                # Assign the retrieved cart_id to the cart object
                cart.id = cart_id

        return cart



        
    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        quantity = int(request.POST.get('quantity', 1))

        user = self.request.user
        cart = self.get_cart()

        # Check if the item is already in the cart
        if user.is_authenticated:
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, user=user, product=product)
        else:
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

        # Update the quantity if the item already exists in the cart
        if not item_created:
            cart_item.quantity = quantity
            cart_item.save()
            # Display a success message for adding the item to the cart
            messages.success(request, "Item added to cart successfully.")
        else:
            # Add the item to the cart if it's a new item
            cart_item.quantity = quantity
            cart_item.save()
            if cart:
                cart.items.add(cart_item)
            # Display a success message for adding the item to the cart
            messages.success(request, "Item added to cart successfully.")

        # Store the quantity in the session
        cart_id = cart.id
        request.session[f'cart_{cart_id}_quantity'] = quantity

        # Subscribe to the newsletter
        newsletter_form = NewsletterSubscriberForm(request.POST)
        if newsletter_form.is_valid():
            newsletter_form.save()
            # Display a success message for subscribing to the newsletter
            messages.success(request, "Successfully subscribed to the newsletter.")

        # Redirect to the same page with the success message
        return HttpResponseRedirect(request.path_info)



class CartPageView(TemplateView):
    template_name = 'store/cart.html'

    def get_cart(self):
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their cart
            cart = Cart.objects.filter(user=self.request.user).first()
        else:
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.filter(id=cart_id).first()
            else:
                cart = Cart.objects.create()
                self.request.session['cart_id'] = cart.id

        return cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve the cart items count for the current user
        cart = self.get_cart()
        context['cart_items_count'] = cart.get_total_items() if cart else 0
        context['wishlist_items_count'] = self.wishlist_items_count()
        cart_items = CartItem.objects.filter(cart=cart)
        context['cart_items'] = cart_items
        context['total_price'] = cart.get_total_price()
        return context

    def wishlist_items_count(self):
        # Logic to retrieve and return the count of items in the wishlist for the current user
        wishlist_items_count = 0
        user = self.request.user
        if user.is_authenticated:
            wishlist_items_count = WishlistItem.objects.filter(wishlist__user=user).count()
        return wishlist_items_count

    def post(self, request, *args, **kwargs):
        cart_item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        # Remove the cart item from the cart
        cart_item.delete()

        messages.success(request, "Item removed from cart successfully.")
        return redirect('cart')
# class SignupView(TemplateView):
#     template_name = 'store/signup.html'


class WishlistView(TemplateView):
    template_name = 'store/wishlist.html'

    def get_wishlist(self):
        if self.request.user.is_authenticated:
            # If the user is logged in, retrieve their wishlist
            wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        else:
            # For anonymous users, retrieve the wishlist from the session
            wishlist_id = self.request.session.get('wishlist_id')
            if wishlist_id:
                wishlist = get_object_or_404(Wishlist, id=wishlist_id)
            else:
                # If the wishlist doesn't exist, create a new one
                wishlist = Wishlist.objects.create()
                self.request.session['wishlist_id'] = wishlist.id

        return wishlist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist = self.get_wishlist()
        context['wishlist_items_count'] = wishlist.items.count()
        context['cart_items_count'] = self.cart_items_count()

        wishlist_items = wishlist.items.all()
        context['wishlist_items'] = wishlist_items

        return context

    def cart_items_count(self):
        # Logic to retrieve and return the cart items count for the current user
        cart_items_count = 0
        user = self.request.user
        if user.is_authenticated:
            cart = Cart.objects.filter(user=user).first()
            if cart:
                cart_items_count = cart.items.count()
        else:
            cart_id = self.request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.filter(id=cart_id).first()
                if cart:
                    cart_items_count = cart.items.count()
        return cart_items_count

    def post(self, request, *args, **kwargs):
        wishlist = self.get_wishlist()
        context = self.get_context_data(**kwargs)

        # # Handling the "Add to Cart" form submission
        # add_to_cart_form = AddToCartForm(request.POST)
        # if add_to_cart_form.is_valid():
        #     product_id = add_to_cart_form.cleaned_data['item_id']
        #     product = get_object_or_404(Product, id=product_id)

        #     # Add the product to the cart (you may need to adjust the logic based on your cart implementation)
        #     cart = self.get_cart()
        #     cart.add_to_cart(product)

        #     messages.success(request, "Item added to cart successfully.")

        # Handling the "Remove from Wishlist" form submission
        remove_from_wishlist_form = RemoveFromWishlistForm(request.POST)
        if remove_from_wishlist_form.is_valid():
            product_id = remove_from_wishlist_form.cleaned_data['item_id']
            product = get_object_or_404(Product, id=product_id)

            # Remove the product from the wishlist
            wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
            if wishlist_item:
                wishlist_item.delete()
                messages.success(request, "Item removed from wishlist successfully.")
            else:
                messages.error(request, "Item is not in the wishlist.")

        return self.get(request, *args, **kwargs)


class ProfileView(View):
    template_name = 'store/profile.html'

    def get(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        context = {'user_profile': user_profile}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Update profile information from the form data
        user_profile.user.first_name = request.POST.get('first_name', '')
        user_profile.user.last_name = request.POST.get('last_name', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.email_notifications_blog = bool(request.POST.get('notifications_blog', False))
        user_profile.email_notifications_news = bool(request.POST.get('notifications_news', False))
        user_profile.email_notifications_offers = bool(request.POST.get('notifications_offers', False))
        user_profile.user.save()
        user_profile.save()

        messages.success(request, 'Profile updated successfully.')

    
        # if request.method == 'POST':
        if 'logout' in request.POST:
            # Manually log out the user
            request.session.flush()
            request.user = User()

            messages.info(request, "You have been logged out.")
        
        return redirect(reverse('profile'))
    
# @csrf_exempt
class PaymentStatusView(View):
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # Process the payment status from Paystack
            response_data = request.POST

            # Check the 'status' field in the response_data to determine the payment status
            status = response_data.get('status')

            if status == 'success':
                # Payment is successful, perform the necessary actions
                # For example, update the order status, create an order, etc.

                # Get the cart items for the current user
                user = request.user
                cart = get_object_or_404(Cart, user=user)

                # Create a new order with the purchased items
                order = Order.objects.create(user=user, total_price=cart.get_subtotal(), status='pending')

                for cart_item in cart.items.all():
                    OrderItem.objects.create(order=order, product=cart_item.product, quantity=cart_item.quantity, unit_price=cart_item.product.discount_price)

                # Clear the cart (remove all items from the cart)
                cart.items.clear()
                cart.is_paid = True
                cart.save()

                # Return a success response to Paystack
                return JsonResponse({'status': 'success'})
            else:
                # Payment failed, handle the failure scenario
                # For example, log the failed payment or take other actions

                # Return an error response to Paystack
                return JsonResponse({'status': 'error', 'message': 'Payment failed'})

        else:
            # Return an error response for invalid request method
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


class OrderDetailView(View):
    template_name = 'store/order.html'

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        return render(request, self.template_name, {'order': order})