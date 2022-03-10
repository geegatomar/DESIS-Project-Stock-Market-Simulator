from django.contrib import admin
from django.urls import path
from . import views

app_name = "stocks"

urlpatterns = [
    path('', views.home, name="home"),
    path('info/<str:id>/', views.info, name="info"),
]
