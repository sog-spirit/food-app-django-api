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
    FavoriteProductSerializer,
    HistorySerializer,
    CouponSerializer,
)
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from .models import (
    User,
    Product,
    Category,
    History,
    Order,
    OrderDetail,
    Cart,
    Review,
    FavoriteProduct,
    Coupon,
    CouponUsage,
)
import jwt
from datetime import date, datetime, timedelta
from .helper import user_authentication, user_permission_authentication

class RegisterView(APIView):
    def post(self, request):
        name = request.data.get('name', None)
        date_of_birth = request.data.get('date_of_birth', None)
        address = request.data.get('address', None)
        email = request.data.get('email', None)
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        phone = request.data.get('phone', None)
        image = request.data.get('image', None)
        if (
            email is None or
            name is None or
            date_of_birth is None or
            address is None or
            username is None or
            password is None or
            phone is None or
            image is None
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
            if image is None:
                message['image'] = 'This field is required'
            response.data = message
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        try:
            user = User.objects.get(username=username)
            return Response(
                {'detail': 'username is existed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            pass

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            phone=phone,
            date_of_birth=date_of_birth,
            name=name,
            address=address,
            image=image,
            balance=1000000,
        )
        History.objects.create(
            _creator = user,
            message = f"???? t???o user {username}",
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
        username = request.data.get('username', None)
        password = request.data.get('password', None)

        if username is None or password is None:
            response = Response()
            message = {}
            if username is None:
                message['username'] = 'This field is required'
            if password is None:
                message['password'] = 'This field is required'
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = message
            return response

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

        token = jwt.encode(payload, 'secret', algorithm='HS256')
        response = Response()
        response.set_cookie(key='jwt', value=token)
        response.data = {
            'jwt': token,
            'user_id': user.id,
            'detail': 'Login successfully',
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        }
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
            message = f"???? update user {user.username}",
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
                message['amount'] = 'This field is required'
            response.data = message
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
        try:
            user = User.objects.get(id=payload['id'])
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
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
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
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

class UserOrderAPIView(APIView):
    def get(self, request, user_id):
        """
        Get orders list
        """
        orders = Order.objects.filter(user=user_id).order_by('-_created')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def delete(self, request, user_id):
        payload = user_authentication(request)
        if payload['id'] != int(user_id):
            return Response(
                {'detail': 'Not this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Order.objects.filter(_creator=user_id).delete()
        return Response(
            {'detail': 'All orders deleted sucessfully'},
            status=status.HTTP_200_OK
        )

class OrderAPIView(APIView):
    def post(self, request):
        payload = user_authentication(request)
        user = User.objects.filter(id=payload['id']).first()
        address = request.data.get('address', None)
        note = request.data.get('note', None)
        shipping_cost = request.data.get('shippingCost', 0)
        order_products = request.data.get('products', None)
        coupon_code = request.data.get('coupon', None)
        if address is None:
            return Response(
                {'detail': 'Address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if order_products is None:
            return Response(
                {'detail': 'products is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(order_products) == 0:
            return Response(
                {'detail': 'products is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        price = 0.0
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
                    message = "???? t???o ????n h??ng",
                )

                for item in request.data['products']:
                    try:
                        product = Product.objects.get(id=item['product'])
                    except Product.DoesNotExist:
                        transaction.set_rollback(True)
                        return Response(
                            {'detail': 'Product not found'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    price += product.price * item['quantity']
                if user.balance < price:
                    transaction.set_rollback(True)
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
                        continue
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                if coupon_code is not None:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        if timezone.now() > coupon.expiry_date:
                            transaction.set_rollback(True)
                            return Response(
                                {'detail': 'Coupon expired'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        try:
                            used_coupon = CouponUsage.objects.get(user=user, coupon=coupon)
                            transaction.set_rollback(True)
                            return Response(
                                {'detail': 'coupon already used'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        except CouponUsage.DoesNotExist:
                            CouponUsage.objects.create(
                                user=user,
                                coupon=coupon
                            )

                        price *= float(1 - (coupon.discount / 100))
                    except Coupon.DoesNotExist:
                        transaction.set_rollback(True)
                        return Response(
                            {'detail': 'invalid coupon code'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
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
    def get(self, request, user_id, order_id):
        order_detail = OrderDetail.objects.filter(order=order_id, _creator=user_id)
        serializer = OrderDetailSerializer(order_detail, many=True)
        return Response(serializer.data)

class UserCoupons(APIView):
    def get(self, request):
        coupons = Coupon.objects.all()
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)

class UserCoupon(APIView):
    def get(self, request, coupon_code):
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if timezone.now() > coupon.expiry_date:
                return Response(
                    {'detail': 'coupon not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            seralizer = CouponSerializer(coupon)
            return Response(seralizer.data)
        except Coupon.DoesNotExist:
            return Response(
                {'detail': 'coupon not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
# NOTE: Not use carts anymore
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
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserReviewAPIView(APIView):
    def get(self, request, user_id):
        reviews = Review.objects.filter(_creator=user_id).order_by('-id')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class ReviewsAPIView(APIView):
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
        data['status'] = 'APPROVE'
        serializer = ReviewSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(id=payload['id']).first()
            History.objects.create(
                _creator=user,
                message='???? review ????n h??ng',
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

class UserGetFavoriteProducts(APIView):
    def get(self, request, user_id):
        products = FavoriteProduct.objects.filter(_creator=user_id, _deleted=None)
        serializer = FavoriteProductSerializer(products, many=True)
        return Response(serializer.data)

class UserFavoriteProduct(APIView):
    def post(self, request):
        payload = user_authentication(request)
        product_id = request.data.get('product', None)
        if product_id is None:
            return Response(
                {'product': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = FavoriteProduct.objects.get(product=product_id, _deleted=None)
            return Response(
                {'detail': 'Favorite product created successfully'},
                status=status.HTTP_200_OK
            )
        except FavoriteProduct.DoesNotExist:
            user = User.objects.get(id=payload['id'])
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'detail': 'Product not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_product = FavoriteProduct.objects.create(_creator=user, product=product)
            return Response(
                {'detail': 'Favorite product created successfully'},
                status=status.HTTP_200_OK
            )

    def delete(self, request):
        payload = user_authentication(request)
        product_id = request.data.get('product', None)
        if product_id is None:
            return Response(
                {'product': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = FavoriteProduct.objects.get(product=product_id, _deleted=None)
            product._deleted = datetime.now()
            product.save()
            return Response(
                {'detail': 'Favorite product deleted successfully'},
                status=status.HTTP_200_OK
            )
        except FavoriteProduct.DoesNotExist:
            return Response(
                {'detail': 'Favorite product already deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminGetOrdersAPIView(APIView):
    def get(self, request):
        """
        Get all orders
        """
        orders = Order.objects.order_by('_creator', '-order_status', '_created')
        serializer = AdminOrderSerializer(orders, many=True)
        return Response(serializer.data)

class AdminOrderAPIView(APIView):
    def get(self, request, order_id):
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
            message = '???? ho??n th??nh ????n h??ng',
        )
        return Response({'detail': 'Order updated successfully'})

class AdminGetReviewsAPIView(APIView):
    def get(self, request, product_id):
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
            message='???? c???p nh???t review'
        )
        return Response({'detail': 'Review updated successfully'})

class AdminUsersAPIView(APIView):
    def get(self, request):
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
        image = request.data.get('image', None)
        if (
            email is None or
            name is None or
            date_of_birth is None or
            address is None or
            username is None or
            password is None or
            phone is None or
            role is None or
            image is None
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
            if image is None:
                message['image'] = 'This field is required'
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
                    image=image,
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
                    image=image,
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
                    image=image
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
            image = request.data.get('image', None)
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
            if image is not None:
                user.image = image
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
                message = "???? t???o s???n ph???m",
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminSingleProductAPIView(APIView):
    def get(self, request, product_id):
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
                message = "???? c???p nh???t s???n ph???m",
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
                message = "???? x??a s???n ph???m",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminCategoriesAPIView(APIView):
    def get(self, request):
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
                message = "???? t???o danh m???c m???i",
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminSingleCategoryAPIView(APIView):
    def get(self, request, category_id):
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
                message = "???? c???p nh???t danh m???c"
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
                message = "???? x??a danh m???c",
            )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminGetProductFromCategory(APIView):
    def get(self, request, category_id):
        products = Product.objects.filter(category=category_id, _deleted=None)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class AdminGetUserHistory(APIView):
    def get(self, request, user_id):
        histories = History.objects.filter(_creator=user_id)
        serializer = HistorySerializer(histories, many=True)
        return Response(serializer.data)

class AdminOverviewStats(APIView):
    def get(self, request):
        all_users_count = User.objects.all().count()
        admin_count = User.objects.filter(is_superuser=True).count()
        staff_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        user_count = User.objects.filter(is_staff=False, is_superuser=False).count()
        order_count = Order.objects.all().count()
        pending_order_count = Order.objects.filter(order_status='PENDING').count()
        done_order_count = Order.objects.filter(order_status='DONE').count()
        done_order_total_money = Order.objects.filter(order_status='DONE').aggregate(Sum('price'))
        return Response(
            {
                'total_user': all_users_count,
                'admin': admin_count,
                'staff': staff_count,
                'user': user_count,
                'total_order': order_count,
                'order_is_doned': done_order_count,
                'order_in_progress': pending_order_count,
                'doned_order_total': done_order_total_money['price__sum']
            },
            status=status.HTTP_200_OK
        )

class AdminLast5DayTotalRevenue(APIView):
    def get(self, request):
        data = {}
        MAX_DATE = 5
        for i in range(0, MAX_DATE + 1):
            data[str(date.today() - timedelta(i))] = 0

        for key in data.keys():
            temp = datetime.strptime(key, '%Y-%m-%d')
            obj_list = Order.objects.filter(
                _created__year=str(temp.year),
                _created__month=str(temp.month),
                _created__day=str(temp.day),
                order_status='DONE'
            ).aggregate(Sum('price'))
            if obj_list['price__sum'] is not None:
                data[key] = obj_list['price__sum']
            else:
                data[key] = 0

        return Response(
            data,
            status=status.HTTP_200_OK
        )
class AdminLast5MonthsRevenue(APIView):
    def get(self, request):
        data = {}
        MAX_MONTH = 5
        temp = date.today()
        for i in range(0, MAX_MONTH + 1):
            data[str(f'{temp.year}-{temp.month}')] = 0
            temp -= timedelta(weeks=4)
        for key in data.keys():
            date_string = str(key).split('-')
            temp_month = date_string[1]
            temp_year = date_string[0]
            obj_list = Order.objects.filter(
                _created__year=str(temp_year),
                _created__month=str(temp_month),
                order_status='DONE'
            ).aggregate(Sum('price'))
            if obj_list['price__sum'] is not None:
                data[key] = obj_list['price__sum']
            else:
                data[key] = 0
        return Response(data)

class AdminCoupons(APIView):
    def get(self, request):
        coupons = Coupon.objects.all()
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)

    def post(self, request):
        payload = user_permission_authentication(request)
        discount = request.data.get('discount', None)
        name = request.data.get('name', None)
        code = request.data.get('code', None)
        expiry_date = request.data.get('expiry_date', None)
        image = request.data.get('image', None)
        if (
            discount is None or
            name is None or
            code is None or
            expiry_date is None
        ):
            response = Response()
            message = {}
            if discount is None:
                message['discount'] = 'This field is required'
            if name is None:
                message['name'] = 'This field is required'
            if code is None:
                message['code'] = 'This field is required'
            if expiry_date is None:
                message['expiry_date'] = 'This field is required'
            response.data = message
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        if int(discount) > 100 or int(discount) <= 0:
            return Response(
                {'detail': 'discount cannot be 0 or greater than 100%'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            coupon = Coupon.objects.get(code=code)
            return Response(
                {'detail': 'code is existed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Coupon.DoesNotExist:
            pass
        coupon = Coupon.objects.create(
            discount=discount,
            name=name,
            code=code,
            expiry_date=expiry_date,
            image=image
        )
        return Response(
            {'detail': 'Coupon created successfully'},
            status=status.HTTP_200_OK
        )

class AdminCoupon(APIView):
    def get(self, request, coupon_id):
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            seralizer = CouponSerializer(coupon)
            return Response(seralizer.data)
        except Coupon.DoesNotExist:
            return Response(
                {'detail': 'coupon not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request, coupon_id):
        payload = user_permission_authentication(request)
        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return Response(
                {'detail': 'Coupon not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        discount = request.data.get('discount', None)
        name = request.data.get('name', None)
        expiry_date = request.data.get('expiry_date', None)
        image = request.data.get('image', None)
        if discount is not None:
            coupon.discount = discount
        if name is not None:
            coupon.name = name
        if expiry_date is not None:
            coupon.expiry_date = expiry_date
        if image is not None:
            coupon.image = image
        coupon.save()
        return Response(
            {'detail': 'coupon edited successfully'},
            status=status.HTTP_200_OK
        )

    def delete(self, request, coupon_id):
        payload = user_permission_authentication(request)
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.delete()
            return Response(
                {'detail': 'coupon deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Coupon.DoesNotExist:
            return Response(
                {'detail': 'coupon not found or deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )