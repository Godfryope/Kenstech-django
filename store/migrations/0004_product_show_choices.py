# Generated by Django 4.2.3 on 2023-07-09 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_alter_product_discount_price_alter_product_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='show_choices',
            field=models.IntegerField(choices=[(10, '10'), (20, '20'), (30, '30'), (40, '40'), (50, '50')], default=10),
        ),
    ]