from django.db import models
from enum import Enum
from stocks.models import Stock
#from base.models import User
#from desisstockmarket import settings
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.
# Specifying the order types as enum since we can only create orders of these specific types.


class OrderTypes(Enum):
    MARKET = "MARKET"
    LIMIT = "SELL"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class OrderDirections(Enum):
    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

# Creating the order table which has a one-to-many relationship with stocks, i.e. many orders can
# correspond to one stock.


class Order(models.Model):
    #orderId = models.CharField(max_length=16, primary_key=True)
    orderType = models.CharField(max_length=255,
                                 choices=OrderTypes.choices(), default=OrderTypes.MARKET)
    orderDirection = models.CharField(max_length=255,
                                      choices=OrderDirections.choices(), default=OrderDirections.BUY)
    orderStatus = models.CharField(max_length=255,
                                   choices=OrderStatus.choices(), default=OrderStatus.PENDING)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    # stockName = models.CharField(max_length=128, unique=True)
    # fullCompanyName = models.CharField(max_length=128)
    # currentSharePrice = models.DecimalField(max_digits=16, decimal_places=3)
    # sharesOutstanding = models.IntegerField()

    # TODO: Add the createdByUser field after users are created
    createdAt = models.DateField(auto_now_add=True)
    updatedAt = models.DateField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,)

    # We are sorting the list to display by the latest createdAt value first
    class Meta:
        ordering = ['-updatedAt', '-createdAt']

    # Note that type 1 is for Market orders, and 2 for limit orders (from enums we defined above)
    def __str__(self):
        return str(self.orderType) + " order to " + str(self.orderDirection) + " " + str(self.quantity) + " " + str(self.stock) + " stock"
