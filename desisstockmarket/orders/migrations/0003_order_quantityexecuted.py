# Generated by Django 4.0.3 on 2022-03-24 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_orderstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='quantityExecuted',
            field=models.IntegerField(default=0),
        ),
    ]