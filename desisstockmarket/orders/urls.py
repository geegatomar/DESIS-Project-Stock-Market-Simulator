from django.contrib import admin
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path('', views.home, name="home"),
    #path('info/<str:id>/', views.info, name="info"),
    path('create-order/', views.createOrder, name="create-order"),
    path('update-order/<str:pk>/', views.updateOrder, name="update-order"),
    path('delete-order/<str:pk>/', views.deleteOrder, name="delete-order"),
    path('create-order-initialized/<str:pk>/<str:direction>/', views.createOrderWithInitialData,
         name="create-order-initialized"),

]
