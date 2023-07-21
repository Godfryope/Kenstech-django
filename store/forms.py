from django import forms
from .models import *

class NewsletterSubscriberForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    # Add other form fields as needed, like product choices or additional options

class DeleteFromCartForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())

class AddToWishlistForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())

class RemoveFromWishlistForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())