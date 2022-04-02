from django.contrib import admin
from django.urls import path
from . import views

app_name = "trades"

urlpatterns = [
    path('view-trades/', views.viewTrades, name="view-trades"),
    path('view-shares/', views.viewUserShares, name='view-shares'),
]
