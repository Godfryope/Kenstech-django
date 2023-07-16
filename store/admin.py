from django.contrib import admin
from .models import *

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Product, ProductAdmin)

admin.site.register(Category)
admin.site.register(ProductImage)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(NewsletterSubscriber)

