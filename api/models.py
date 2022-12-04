from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
# TODO: coupon model

class User(AbstractUser):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    image = models.ImageField(blank=True, null=True, upload_to='user_image')
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    balance = models.FloatField(default=0.0)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['password', 'email', 'phone']

class Category(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category_updater")
    _deleted = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(blank=True, null=True, upload_to='category_image')

    def __str__(self):
        return self.name

class Product(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="product_updater")
    _deleted = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=500, null=True, blank=True)
    price = models.FloatField(default=0.0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_fk')
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    PRODUCT_STATUS = [
        ("D", "DISABLE"),
        ("E", "ENABLE"),
    ]
    status = models.CharField(max_length=10, choices=PRODUCT_STATUS, default="E")

    def __str__(self):
        return self.name + ', id ' + str(self.id)

class Order(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_updater")
    _deleted = models.DateTimeField(null=True, blank=True)
    price = models.FloatField(default=0.0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_user_fk')
    PAYMENT_METHOD_ENUM = [
        ("COD", "COD"),
        ("BANKING", "BANKING")
    ]
    ORDER_STATUS_ENUM = [
        ("PENDING", "PENDING"),
        ("DONE", "DONE")
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_ENUM, default="COD")
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS_ENUM, default="PENDING")
    address = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return "Order id {id}".format(id=self.id)

class Review(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_updater")
    _deleted = models.DateTimeField(blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='review_order_fk')
    content = models.TextField(null=True, blank=True)
    rating = models.FloatField()
    REVIEW_STATUS = [
        ("PENDING", "PENDING"),
        ("APPROVE", "APPROVE")
    ]
    status = models.CharField(max_length=7, choices=REVIEW_STATUS, default="PENDING")

    def __str__(self):
        return "Review id {review_id} of order id {order_id}".format(review_id=self.id, order_id=self.order.id)

class OrderDetail(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detail_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="detail_updater")
    _deleted = models.DateTimeField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_product_details')
    quantity = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='detail_order_fk')
    
    def __str__(self):
        return 'Order detail id {id} of order id {order_id} for product id {product_id}'.format(id=self.id, order_id=self.order, product_id=self.product.id)

class Cart(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_creator')
    _updated = models.DateTimeField(auto_now=True)
    _updater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_updater")
    _deleted = models.DateTimeField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_item')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f'Cart item id {self.product.id}, user id {self._creator.id}, quantity {self.quantity}'

class History(models.Model):
    _created = models.DateTimeField(auto_now_add=True)
    _creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history_creator')
    message = models.TextField(null=True, blank=True)

# class Coupon(models.Model):
#     discount = models.IntegerField(default=0)
#     name = models.CharField(max_length=255)