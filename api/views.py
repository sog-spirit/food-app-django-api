from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework import status
from .serializers import (
    UserSerializer,
    ProductSerializer,
    CategorySerializer,
    OrderDetailSerializer,
    OrderSerializer,
    AdminOrderSerializer,
    CartSerializer,
    ReviewSerializer,
    AdminUserSerializer,
)
from django.db import IntegrityError, transaction
from .models import (
    User,
    Product,
    Category,
    History,
    Order,
    OrderDetail,
    Cart,
    Review,
)
import jwt
from datetime import datetime, timedelta
from .helper import user_authentication, user_permission_authentication

class RegisterView(APIView):
    """
    Required fields:
    email
    username
    password
    phone
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(
            email=request.data['email'],
            username=request.data['username'],
            password=request.data['password'],
            phone=request.data['phone'],
        )
        History.objects.create(
            _creator = user,
            message = "create new user",
        )
        return Response(
            {
                'detail': 'User created successfully',
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):
    """
    Required fields:
    username
    password
    """
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        user = User.objects.filter(username=username).first()

        if user is None:
            raise AuthenticationFailed('User not found')
        
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password')

        if user.is_active is False:
            raise AuthenticationFailed('Username or password is invalid')
        
        payload = {
            'id': user.id,
            'exp': datetime.utcnow() + timedelta(minutes=60),
            'iat': datetime.utcnow()
        }
        if user.is_superuser:
            user_role = 'Admin'
        elif user.is_staff:
            user_role = 'Staff'
        else:
            user_role = 'Customer'
        
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        response = Response()
        response.set_cookie(key='jwt', value=token)
        response.data = {
            'jwt': token,
            'detail': 'Login successfully'
        }
        History.objects.create(
            _creator = user,
            message = "was login",
        )
        return response

class UpdateUserView(APIView):
    """
    Any fields defined in User class from models.py
    """
    def patch(self, request):
        payload = user_authentication(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        History.objects.create(
            _creator = user,
            message = "update user",
        )
        return Response(
            {
                'detail': 'User info updated successfully'
            }
        )

class UpdatePasswordView(APIView):
    def patch(self, request):
        payload = user_authentication(request)
        user = User.objects.filter(id=payload['id']).first()
        current_password = request.data.get('current_password', None)
        new_password = request.data.get('new_password', None)
        if current_password is None or new_password is None:
            response = Response()
            message = {}
            if current_password is None:
                message['current_password'] = 'This field is required'
            if new_password is None:
                message['new_password'] = 'This field is required'
            response.data = message
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
        if user.check_password(current_password) is False:
            return Response(
                {'detail': 'Current password is invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(
            {'detail': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )

class UpdateUserBalanceView(APIView):
    def patch(self, request):
        payload = user_authentication(request)
        current_password = request.data.get('current_password', None)
        amount = request.data.get('amount', None)
        if current_password is None or amount is None:
            response = Response()
            message = {}
            if current_password is None:
                message['current_password'] = 'This field is required'
            if amount is None:
                message['new_password'] = 'This field is required'
            response.data = message
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
        user = User.objects.filter(id=payload['id']).first()
        if user.check_password(current_password) is False:
            return Response(
                {'detail': 'Current password is invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            amount = float(amount)
        except ValueError:
            return Response(
                {'detail': 'Amount is not a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if amount <= 0:
            return Response(
                {'detail': 'Amount must be a positive number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.balance += amount
        user.save()
        return Response(
            {'detail': 'Balance added successfully'},
            status=status.HTTP_200_OK
        )

class UserView(APIView):
    def get(self, request):
        payload = user_authentication(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)

        return Response(serializer.data)

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'detail': 'Logout successfully'
        }

        return response

class ProductsAPIView(APIView):
    def get(self, request):
        products = Product.objects.all().filter(_deleted=None)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class SingleProductAPIView(APIView):
    def get(self, request, id):
        product = Product.objects.get(id=id)
        serializer = ProductSerializer(product, many=False)

        if product._deleted == None:
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(None, status=status.HTTP_400_BAD_REQUEST)

class CategoriesAPIView(APIView):
    def get(self, request):
        categories = Category.objects.all().filter(_deleted=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class SingleCategoryAPIView(APIView):
    def get(self, request, id):
        data = request.data
        category = Category.objects.get(id=id)
        serializer = CategorySerializer(category, many=False)

        if category._deleted == None:
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(None, status=status.HTTP_400_BAD_REQUEST)

class GetProductFromCategory(APIView):
    def get(self, request, category_id):
        products = Product.objects.filter(category=category_id, _deleted=None)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class OrderAPIView(APIView):
    def get(self, request):
        """
        Get orders list
        """
        payload = user_authentication(request)
        orders = Order.objects.filter(user=payload['id']).order_by('-_created')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        payload = user_authentication(request)
        user = User.objects.filter(id=payload['id']).first()
        address = request.data.get('address', None)
        note = request.data.get('note', None)
        shipping_cost = request.data.get('shippingCost', 0)
        if address is None:
            return Response(
                {'detail': 'Address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        price = 0.0

        for item in request.data['products']:
            print(item)
        
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    _creator = user,
                    _updater = user,
                    user = user,
                    address=address,
                    note=note
                )

                History.objects.create(
                    _creator = user,
                    message = "create order",
                )

                for item in request.data['products']:
                    product = Product.objects.filter(id=item['product']).first()
                    price += product.price * item['quantity']
                if user.balance < price:
                    return Response(
                        {'detail': 'Account balance is insufficient'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                for item in request.data['products']:
                    product = Product.objects.filter(id=item['product']).first()
                    data = item.copy()
                    data['_creator'] = payload['id']
                    data['_updater'] = payload['id']
                    data['order'] = order.id

                    # cart_item = Cart.objects.filter(
                    #     product=product,
                    #     _creator=user,
                    #     _deleted=None
                    #     ).first()
                    # cart_item._deleted = datetime.now()
                    # cart_item._updater = user
                    # cart_item.save()

                    serializer = OrderDetailSerializer(data=data)

                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        History.objects.create(
                            _creator = user,
                            message = "create order detail"
                        )
                        continue
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                price += shipping_cost
                order.price = price
                order.save()
                user.balance -= price
                user.save()

        except IntegrityError:
            return Response({'detail': 'Query error'},status=status.HTTP_400_BAD_REQUEST)

        except KeyError:
            return Response({'detail': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(request.data)

class OrderDetailAPIView(APIView):
    def get(self, request, order_id):
        payload = user_authentication(request)
        order_detail = OrderDetail.objects.filter(order=order_id, _creator=payload['id'])
        serializer = OrderDetailSerializer(order_detail, many=True)
        return Response(serializer.data)

class CartsAPIView(APIView):
    def get(self, request):
        payload = user_authentication(request)
        cart_items = Cart.objects.filter(_deleted=None, _creator=payload['id'])
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        payload = user_authentication(request)
        
        data = request.data.copy()
        data['_creator'] = payload['id']
        data['_updater'] = payload['id']
        user = User.objects.filter(id=payload['id']).first()
        product_id = request.data.get('product', None)
        if product_id is None:
            return Response(
                {'detail': 'product is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            cart_item = Cart.objects.get(product=product_id, _deleted=None, _creator=payload['id'])
            cart_item_quantity = request.data.get('quantity', None)
            if cart_item_quantity is None:
                return Response(
                    {'detail': 'quantity is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity += int(cart_item_quantity)
            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        except Cart.DoesNotExist:
            pass

        try:
            with transaction.atomic():
                serializer = CartSerializer(data=data)

                if serializer.is_valid():
                    serializer.save()
                    History.objects.create(
                        _creator = user,
                        message = "create cart item"
                    )
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError:
            return Response({'detail': 'Error creating cart item'}, status=status.HTTP_400_BAD_REQUEST)

class SingleCartAPIView(APIView):
    def delete(self, request, cart_id):
        payload = user_authentication(request)
        
        cart_item = Cart.objects.filter(id=cart_id, _creator=payload['id']).first()

        if cart_item._deleted is not None:
            return Response({
                'detail': 'Cart item is already deleted'
            },
            status=status.HTTP_400_BAD_REQUEST)

        serializer = CartSerializer(
            instance=cart_item,
            data = {
                '_deleted': datetime.now(),
                '_updater': payload['id']
            },
            partial = True
        )

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "delete cart item"
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, cart_id):
        payload = user_authentication(request)
        
        data = request.data.copy()
        cart_item = Cart.objects.get(id=cart_id, _creator=payload['id'])
        if cart_item._deleted is not None:
            return Response({
                'detail': 'Cart item is already deleted'
            },
            status = status.HTTP_400_BAD_REQUEST)
        
        serializer = CartSerializer(instance=cart_item, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "Update cart item",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetProductOnCartAPIView(APIView):
    def get(self, request, product_id):
        payload = user_authentication(request)
        try:
            cart_item = Cart.objects.get(product=product_id, _deleted=None, _creator=payload['id'])
        except Cart.DoesNotExist:
            return Response(
                {},
                status=status.HTTP_200_OK
            )
        serializer = CartSerializer(cart_item)
        return Response(serializer.data)
    
    def put(self, request, product_id):
        payload = user_authentication(request)
        
        data = request.data.copy()
        try:
            cart_item = Cart.objects.get(product=product_id, _deleted=None, _creator=payload['id'])
        except Cart.DoesNotExist:
            return Response(
                {'detail': 'cart item does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CartSerializer(instance=cart_item, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "Update cart item",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewsAPIView(APIView):
    def get(self, request):
        payload = user_authentication(request)
        reviews = Review.objects.filter(_creator=payload['id']).order_by('-id')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        order_id = request.data.get('order', None)
        if order_id is None:
            return Response(
                {'detail': 'order is required'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            review = Review.objects.get(order=order_id)
            return Response(
                {'detail': 'Review for this order is existed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Review.DoesNotExist:
            pass
        payload = user_authentication(request)
        order = Order.objects.filter(id=order_id).first()
        if order.user.id != payload['id']:
            return Response(
                {'detail': 'Not user order'},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data.copy()
        data['_creator'] = payload['id']
        data['_updater'] = payload['id']
        serializer = ReviewSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator=user,
                message='review created',
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewsFromProductAPIView(APIView):
    def get(self, request, product_id):
        order_details = OrderDetail.objects.filter(product=product_id)
        orders = Order.objects.filter(id__in=order_details.values_list('order', flat=True))
        reviews = Review.objects.filter(order__in=orders.values_list('id', flat=True), status='APPROVE')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class AdminGetOrdersAPIView(APIView):
    def get(self, request):
        """
        Get all orders
        """
        payload = user_permission_authentication(request)
        orders = Order.objects.order_by('_creator', '-order_status', '_created')
        serializer = AdminOrderSerializer(orders, many=True)
        return Response(serializer.data)

class AdminOrderAPIView(APIView):
    def get(self, request, order_id):
        payload = user_permission_authentication(request)
        order_detail = OrderDetail.objects.filter(order=order_id)
        serializer = OrderDetailSerializer(order_detail, many=True)
        return Response(serializer.data)

    def patch(self, request, order_id):
        payload = user_permission_authentication(request)
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AdminOrderSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = User.objects.filter(id=payload['id']).first()
        History.objects.create(
            _creator=user,
            message = 'update order',
        )
        return Response({'detail': 'Order updated successfully'})

class AdminGetReviewsAPIView(APIView):
    def get(self, request, product_id):
        payload = user_permission_authentication(request)
        order_details = OrderDetail.objects.filter(product=product_id)
        orders = Order.objects.filter(id__in=order_details.values_list('order', flat=True))
        reviews = Review.objects.filter(order__in=orders.values_list('id', flat=True))
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class AdminEditReviewsAPIView(APIView):
    def patch(self, request, review_id):
        payload = user_permission_authentication(request)
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'detail': 'Review does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = User.objects.filter(id=payload['id']).first()
        History.objects.create(
            _creator=user,
            message='update review'
        )
        return Response({'detail': 'Review updated successfully'})

class AdminUsersAPIView(APIView):
    def get(self, request):
        payload = user_permission_authentication(request)
        users = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create user
        """
        payload = user_permission_authentication(request)
        name = request.data.get('name', None)
        date_of_birth = request.data.get('date_of_birth', None)
        address = request.data.get('address', None)
        email = request.data.get('email', None)
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        phone = request.data.get('phone', None)
        role = request.data.get('role', None)
        if (
            email is None or
            name is None or
            date_of_birth is None or
            address is None or
            username is None or
            password is None or
            phone is None or
            role is None
        ):
            response = Response()
            message = {}
            if name is None:
                message['name'] = 'This field is required'
            if date_of_birth is None:
                message['date_of_birth'] = 'This field is required'
            if address is None:
                message['address'] = 'This field is required'
            if email is None:
                message['email'] = 'This field is required'
            if username is None:
                message['username'] = 'This field is required'
            if password is None:
                message['password'] = 'This field is required'
            if phone is None:
                message['phone'] = 'This field is required'
            if role is None:
                message['role'] = 'This field is required'
            response.data = message
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        try:
            user = User.objects.get(username=username)
            return Response(
                {'detail': 'Username is existed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            if role == 'admin':
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    phone=phone,
                    name=name,
                    date_of_birth=date_of_birth,
                    address=address,
                    is_superuser=True
                )
            elif role == 'staff':
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    phone=phone,
                    name=name,
                    date_of_birth=date_of_birth,
                    address=address,
                    is_staff=True
                )
            else:
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    phone=phone,
                    name=name,
                    date_of_birth=date_of_birth,
                    address=address,
                )
            return Response(
                {'detail': 'User created successfully'},
                status=status.HTTP_200_OK
            )

class AdminUserAPIView(APIView):
    def get(self, request, user_id):
        """
        Get single user by user id
        """
        payload = user_permission_authentication(request)
        try:
            user = User.objects.get(id=user_id)
            serializer = AdminUserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, user_id):
        """
        Update user
        """
        payload = user_permission_authentication(request)
        try:
            user = User.objects.get(id=user_id)
            name = request.data.get('name', None)
            role = request.data.get('role', None)
            email = request.data.get('email', None)
            phone = request.data.get('phone', None)
            address = request.data.get('address', None)
            date_of_birth = request.data.get('date_of_birth', None)
            password = request.data.get('password', None)
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if password is not None:
                user.set_password(password)
            if phone is not None:
                user.phone = phone
            if address is not None:
                user.address = address
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth
            if role is not None:
                if role == 'admin':
                    user.is_superuser = True
                    user.is_staff = False
                elif role == 'staff':
                    user.is_superuser = False
                    user.is_staff = True
                else:
                    user.is_superuser = False
                    user.is_staff = False
            user.save()
            return Response(
                {'detail': 'User updated successfully'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, user_id):
        """
        Delete user
        """
        payload = user_permission_authentication(request)
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return Response(
                {'detail': 'User deleted successfully'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminProductsAPIView(APIView):
    def get(self, request):
        payload = user_permission_authentication(request)
        products = Product.objects.all().filter(_deleted=None)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    """
    Required:
    category
    _creator (auto created with user id)
    _updater (auto created with user id)
    """
    def post(self, request):
        payload = user_permission_authentication(request)
        data = request.data.copy()
        data['_creator'] = payload['id']
        data['_updater'] = payload['id']
        serializer = ProductSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "create new product",
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminSingleProductAPIView(APIView):
    def get(self, request, product_id):
        payload = user_permission_authentication(request)
        product = Product.objects.get(id=product_id)
        serializer = ProductSerializer(product, many=False)

        if product._deleted == None:
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(None, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, product_id):
        payload = user_permission_authentication(request)
        data = request.data.copy()
        data['_updater'] = payload['id']
        product = Product.objects.get(id=product_id)
        if product._deleted is not None:
            return Response({
                'detail': 'Product is already deleted'
            },
            status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProductSerializer(instance=product, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "update product",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        payload = user_permission_authentication(request)
        product = Product.objects.get(id=product_id)
        if product._deleted is not None:
            return Response({
                'detail': 'Product is already deleted'
            },
            status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductSerializer(
            instance=product,
            data={
                "_deleted": datetime.now(),
                '_updater': payload['id']
            },
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "delete product",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminCategoriesAPIView(APIView):
    def get(self, request):
        payload = user_permission_authentication(request)
        categories = Category.objects.all().filter(_deleted=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    """
    Required fields:
    name
    _creator (auto created with user id)
    _updater (auto created with user id)
    """
    def post(self, request):
        payload = user_permission_authentication(request)
        data = request.data.copy()
        data['_creator'] = payload['id']
        data['_updater'] = payload['id']
        serializer = CategorySerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "create new category",
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminSingleCategoryAPIView(APIView):
    def get(self, request, category_id):
        payload = user_permission_authentication(request)
        category = Category.objects.get(id=category_id)
        serializer = CategorySerializer(category, many=False)

        if category._deleted == None:
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(None, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, category_id):
        payload = user_permission_authentication(request)
        data = request.data
        data['_updater'] = payload['id']
        category = Category.objects.get(id=category_id)
        if category._deleted is not None:
            return Response({
                'detail': 'Category is already deleted'
            },
            status=status.HTTP_400_BAD_REQUEST)
        serializer = CategorySerializer(instance=category, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "update category",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, category_id):
        payload = user_permission_authentication(request)
        category = Category.objects.get(id=category_id)
        if category._deleted is not None:
            return Response({
                'detail': 'Category is already deleted'
            },
            status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CategorySerializer(
            instance=category,
            data={
                '_deleted': datetime.now(),
                '_updater': payload['id']
            },
            partial=True)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator = user,
                message = "delete category",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminGetProductFromCategory(APIView):
    def get(self, request, category_id):
        payload = user_permission_authentication(request)
        products = Product.objects.filter(category=category_id, _deleted=None)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)