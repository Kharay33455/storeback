from django.contrib import admin
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.store, name='store'),
    path('categories/new-arrivals', views.new, name='new'),

    path('profile/', views.profile, name= 'profile'),
    path('product/<slug:prodslug>/', views.product, name= 'product'),
    path('more/<slug:prodslug>/', views.more, name="more"),
    path('categories/<slug:catslug>/<slug:prodslug>/details/', views.details, name= 'details'),


    path('categories/', views.category, name= 'category'),
    path('categories/<slug:slug>/', views.cat, name= 'cat'),
    path('cart/', views.cart, name='cart'),
    path('cart/<int:id>/<slug:do>', views.update, name='update'),
    path('checkout/', views.checkout, name='checkout'),
    path('add-to-cart/', views.add_to_cart, name='add'),
    path('payment/<int:tfid>/', views.payment, name = 'payment'),
    path('create-shipping/<slug:coe>/', views.create_shipping, name = 'create-ship'),
    path('checkout/update-details/', views.change, name = 'change'),
    path('cart/empty', views.empty, name='empty'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('register/', views.registration_request, name='register'),
    path('<slug:catslug>/test', views.test, name='test'),
    path('cat-frame/', views.catframe, name='catframe'),
    path('search/', views.search, name='search'),
    path("get-global-context", views.get_global_context, name= "get-global-context"),
    path("retrieve", views.retrieve, name="retrieve"),
    path("get-otp", views.getOtp, name="get-otp"),
    path("get-cart-data", views.getCart, name ="get-cart-data"),
    path("has-paid/<slug:orderId>/", views.has_paid, name = "has_paid"),
    path("history", views.history, name = "history"),
    path("summary/<slug:order_id>", views.summary, name = "summary")
]