from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
# from django.dispatch import receiver
# from svglib.svglib import svg2rlg
# from reportlab.graphics import renderPM
# import os
# import tempfile
# from wand.image import Image



class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    discount_price = models.IntegerField(default=0)
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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# def convert_image_to_svg(image_path):
#     # Create a temporary file with .svg extension
#     _, temp_svg_path = tempfile.mkstemp(suffix='.svg')

#     # Convert the image to SVG format using wand library
#     with Image(filename=image_path) as img:
#         img.format = 'svg'
#         img.save(filename=temp_svg_path)

#     # Return the path of the converted SVG file
#     return temp_svg_path

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='products', blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # # Convert the uploaded image to SVG format
        # if self.image and not self.image:
        #     svg_path = convert_image_to_svg(self.image.path)
        #     self.image.save(os.path.basename(svg_path), open(svg_path, 'rb'))

        #     # Remove the temporary SVG file
        #     os.remove(svg_path)

        super().save(*args, **kwargs)




    
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

    
