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
    LIMIT = "LIMIT"

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
    # The dynamicQuantity field is used for the execution of orders
    dynamicQuantity = models.IntegerField(default=1)
    # TODO: Dont display limit price to user if they select 'market' orders
    limitPrice = models.DecimalField(
        max_digits=16, decimal_places=3, blank=True)

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
        price = str(" at Limit " + str(self.limitPrice) if self.orderType ==
                    'LIMIT' else "")
        # orderStatus = ("PENDING" if self.orderStatus ==
        #                'OrderStatus.PENDING' else "EXECUTED")
        orderStatus = ('EXECUTED' if self.orderStatus in (
            'OrderStatus.EXECUTED', 'EXECUTED', OrderStatus.EXECUTED) else 'PENDING')
        return str(self.orderType) + " order to " + str(self.orderDirection) + " " + str(self.quantity) + " " + str(self.stock) + " stock" + price + ": " + orderStatus
