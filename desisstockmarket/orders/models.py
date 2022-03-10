from django.db import models
from enum import Enum
from stocks.models import Stock

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

# Creating the order table which has a one-to-many relationship with stocks, i.e. many orders can
# correspond to one stock.


class Order(models.Model):
    orderId = models.CharField(max_length=16, primary_key=True)
    orderType = models.CharField(max_length=255,
                                 choices=OrderTypes.choices(), default=OrderTypes.MARKET)
    orderDirection = models.CharField(max_length=255,
                                      choices=OrderDirections.choices(), default=OrderDirections.BUY)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    # stockName = models.CharField(max_length=128, unique=True)
    # fullCompanyName = models.CharField(max_length=128)
    # currentSharePrice = models.DecimalField(max_digits=16, decimal_places=3)
    # sharesOutstanding = models.IntegerField()

    # TODO: Add the createdByUser field after users are created
    createdAt = models.DateField(auto_now_add=True)
    updatedAt = models.DateField(auto_now=True)

    # We are sorting the list to display by the latest createdAt value first
    class Meta:
        ordering = ['-updatedAt', '-createdAt', '-orderId']

    # Note that type 1 is for Market orders, and 2 for limit orders (from enums we defined above)
    def __str__(self):
        orderType = "MARKET" if self.orderType == OrderTypes.MARKET else "LIMIT"
        orderDirection = "BUY" if self.orderDirection == OrderDirections.BUY else "SELL"
        return str(orderType) + " order to " + str(orderDirection) + " " + str(self.quantity) + " " + str(self.stock) + " stock"
