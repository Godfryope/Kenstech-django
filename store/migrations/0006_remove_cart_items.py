# Generated by Django 4.1.7 on 2023-06-29 02:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_product_related_products'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='items',
        ),
    ]