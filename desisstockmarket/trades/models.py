from django.db import models
from enum import Enum
from stocks.models import Stock
#from base.models import User
#from desisstockmarket import settings
from django.conf import settings
from orders.models import Order

from django.contrib.auth import get_user_model
User = get_user_model()

# An order transitions to a trade state once it gets executed


class Trade(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    executionPrice = models.DecimalField(max_digits=16, decimal_places=3)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    # I need user field here to be able to filter out the trades for a particular user
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,)
    profit = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    # We are sorting the list to display by the latest createdAt value first
    class Meta:
        ordering = ['-createdAt']

    # Note that type 1 is for Market orders, and 2 for limit orders (from enums we defined above)
    def __str__(self):
        return "Order " + str(self.order) + " executed at price: " + str(self.executionPrice)

class Shares_Owned(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    avg_cost_price = models.DecimalField(max_digits=16, decimal_places=3, default=0)

    def __str__(self):
        return "User " + str(self.user.username) + " Stock: " + str(self.stock.stockName)