# Generated manually for updating ShippingAddress country field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_add_shipping_and_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shippingaddress',
            name='country',
            field=models.CharField(blank=True, default='India', max_length=100),
        ),
    ]
