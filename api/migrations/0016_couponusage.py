# Generated by Django 4.0.4 on 2022-12-21 14:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_coupon'),
    ]

    operations = [
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_fk', to='api.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_fk', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
