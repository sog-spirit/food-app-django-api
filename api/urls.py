from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    UserView,
    LogoutView,
    UpdateUserView,
    UpdatePasswordView,
    UpdateUserBalanceView,
    ProductsAPIView,
    SingleProductAPIView,
    CategoriesAPIView,
    SingleCategoryAPIView,
    GetProductFromCategory,
    UserOrderAPIView,
    OrderAPIView,
    OrderDetailAPIView,
    CartsAPIView,
    SingleCartAPIView,
    GetProductOnCartAPIView,
    UserReviewAPIView,
    ReviewsAPIView,
    ReviewsFromProductAPIView,
    UserGetFavoriteProducts,
    UserFavoriteProduct,
    AdminProductsAPIView,
    AdminSingleProductAPIView,
    AdminCategoriesAPIView,
    AdminSingleCategoryAPIView,
    AdminGetProductFromCategory,
    AdminGetOrdersAPIView,
    AdminOrderAPIView,
    AdminGetReviewsAPIView,
    AdminEditReviewsAPIView,
    AdminUsersAPIView,
    AdminUserAPIView,
)

urlpatterns = [
    path('user/register', RegisterView.as_view()),
    path('user/login', LoginView.as_view()),
    path('user/<int:user_id>', UserView.as_view()),
    path('user/logout', LogoutView.as_view()),
    path('user/update', UpdateUserView.as_view()),
    path('user/update/password', UpdatePasswordView.as_view()),
    path('user/update/balance', UpdateUserBalanceView.as_view()),
    path('product', ProductsAPIView.as_view()),
    path('product/<str:id>', SingleProductAPIView.as_view()),
    path('category', CategoriesAPIView.as_view()),
    path('category/<str:id>', SingleCategoryAPIView.as_view()),
    path('category/detail/<int:category_id>', GetProductFromCategory.as_view()),
    path('user/<str:user_id>/order', UserOrderAPIView.as_view()),
    path('order', OrderAPIView.as_view()),
    path('user/<str:user_id>/order/<int:order_id>', OrderDetailAPIView.as_view()),
    path('cart', CartsAPIView.as_view()),
    path('cart/<int:cart_id>', SingleCartAPIView.as_view()),
    path('cart/product/<int:product_id>', GetProductOnCartAPIView.as_view()),
    path('user/<str:user_id>/review', UserReviewAPIView.as_view()),
    path('review', ReviewsAPIView.as_view()),
    path('user/<int:user_id>/favorites', UserGetFavoriteProducts.as_view()),
    path('user/favorite', UserFavoriteProduct.as_view()),
    path('product/<int:product_id>/review', ReviewsFromProductAPIView.as_view()),
    path('admin/product', AdminProductsAPIView.as_view()),
    path('admin/product/<int:product_id>', AdminSingleProductAPIView.as_view()),
    path('admin/category', AdminCategoriesAPIView.as_view()),
    path('admin/category/<int:category_id>', AdminSingleCategoryAPIView.as_view()),
    path('admin/category/detail/<int:category_id>', AdminGetProductFromCategory.as_view()),
    path('admin/orders', AdminGetOrdersAPIView.as_view()),
    path('admin/orders/detail/<int:order_id>', AdminOrderAPIView.as_view()),
    path('admin/product/<int:product_id>/reviews', AdminGetReviewsAPIView.as_view()),
    path('admin/reviews/<int:review_id>', AdminEditReviewsAPIView.as_view()),
    path('admin/users', AdminUsersAPIView.as_view()),
    path('admin/users/<int:user_id>', AdminUserAPIView.as_view()),
]