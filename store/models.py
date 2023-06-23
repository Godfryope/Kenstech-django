from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    categories = models.ManyToManyField(Category)
    description = models.TextField()
    details = models.TextField()
    # size = models.CharField(max_length=20, blank=True, null=True)
    # color = models.CharField(max_length=20, blank=True, null=True)
    # quantity = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=True)
    hot_deal= models.BooleanField(default=False)
    sales = models.IntegerField(default=0)
    slug = models.SlugField(unique=True, null=True, blank=True)

    # Add user session relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"
    
class NewsletterSubscriber(models.Model):
    email = models.EmailField()

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField()

    # Add user session relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Review for {self.product.name}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"



class Cart(models.Model):
    items = models.ManyToManyField(CartItem)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    def get_total_items(self):
        return self.items.count()

    def get_subtotal(self):
        subtotal = sum(item.product.price * item.quantity for item in self.items.all())
        return subtotal

    def get_total_price(self):
        total_price = self.get_subtotal()
        return total_price
