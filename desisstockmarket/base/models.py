from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    account_value = models.DecimalField(
        max_digits=20, decimal_places=3, default=100000)
    USERNAME_FIELD = 'username'
