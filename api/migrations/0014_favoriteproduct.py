# Generated by Django 4.0.4 on 2022-12-10 05:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_alter_category_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_created', models.DateTimeField(auto_now_add=True)),
                ('_deleted', models.DateTimeField(blank=True, null=True)),
                ('_creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_product_creator', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_product_fk', to='api.product')),
            ],
        ),
    ]
