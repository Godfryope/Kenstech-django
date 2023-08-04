from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image



class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_value = models.PositiveIntegerField(default=0)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    discount = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category)
    related_products = models.ManyToManyField('self', blank=True)
    timestamp = models.TimeField(auto_now=False, auto_now_add=True)
    description = models.TextField()
    details = models.TextField()
    # size = models.CharField(max_length=20, blank=True, null=True)
    # color = models.CharField(max_length=20, blank=True, null=True)
    # quantity = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=True)
    hot_deal= models.BooleanField(default=False)
    sales = models.IntegerField(default=0)
    shipping_fee = models.IntegerField(default=0)
    slug = models.SlugField(unique=True, null=True, blank=True)

    # Add user session relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
    
    # def save(self, *args, **kwargs):
    #     self.sales = self.cartitem_set.aggregate(total_count=models.Sum('quantity'))['total_count'] or 0
    #     super().save(*args, **kwargs)
    

    def save(self, *args, **kwargs):
        if self.discount:
            discount_amount = self.price * self.discount_value / 100
            self.discount_price = self.price - discount_amount
        else:
            self.discount_price = self.price

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

        

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products', blank=True, null=True)

    def optimize_image(self):
        if self.image:
            img = Image.open(self.image.path)
            img.thumbnail((250, 250))  # Resize the image to a maximum size of 800x800 pixels
            img.save(self.image.path, optimize=True, quality=90)  # Optimize and save the image

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            # Optimize the product image after saving
            self.optimize_image()

        super().save(*args, **kwargs)

        # # Optimize the product image after saving
        # self.optimize_image()

    




    
class NewsletterSubscriber(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField()

    # Add user session relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Review for {self.product.name}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    def __str__(self):
        return f"{self.quantity} x {self.product.name}"



class Cart(models.Model):
    items = models.ManyToManyField(CartItem)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    def get_total_items(self):
        return self.items.count()

    def get_subtotal(self):
        subtotal = sum(
            item.product.discount_price * item.quantity if item.product.discount else item.product.price * item.quantity
            for item in self.items.all()
        )
        # subtotal = sum(item.product.price * item.quantity for item in self.items.all())
        return subtotal

    def get_total_price(self):
        total_price = self.get_subtotal()
        return total_price


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} in wishlist"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    email_notifications_blog = models.BooleanField(default=True)
    email_notifications_news = models.BooleanField(default=True)
    email_notifications_offers = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='OrderItem')
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.product.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.unit_price})"