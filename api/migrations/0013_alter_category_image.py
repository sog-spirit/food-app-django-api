# Generated by Django 4.0.4 on 2022-12-08 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_user_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
