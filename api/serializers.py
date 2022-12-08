from rest_framework import serializers
from .models import User, Product, Category, Order, OrderDetail, Cart, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            'date_joined',
            'is_active',
            'first_name',
            'last_name',
            'last_login',
            'password',
            'balance',
            'is_superuser',
            'is_staff',
            'groups',
            'user_permissions',
        )
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.address = validated_data.get('address', instance.address)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Product
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class AdminOrderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='_creator.name', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

class OrderDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    image = serializers.CharField(source='product.image', read_only=True)
    price = serializers.FloatField(source='product.price', read_only=True)

    class Meta:
        model = OrderDetail
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    image = serializers.CharField(source='product.image', read_only=True)
    price = serializers.FloatField(source='product.price', read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='_creator.name', read_only=True)
    email = serializers.CharField(source='_creator.email', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'

class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = (
            'first_name',
            'last_name',
            'last_login',
            'password',
            'balance',
            'is_superuser',
            'is_staff',
            'groups',
            'user_permissions',
        )

    def get_role(self, instance):
        if instance.is_superuser is True:
            return 'admin'
        if instance.is_staff is True:
            return 'staff'
        return 'user'