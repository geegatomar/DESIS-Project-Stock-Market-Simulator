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
    createdAt = models.DateField(auto_now_add=True)
    updatedAt = models.DateField(auto_now=True)
    # I need user field here to be able to filter out the trades for a particular user
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,)

    # We are sorting the list to display by the latest createdAt value first
    class Meta:
        ordering = ['-createdAt']

    # Note that type 1 is for Market orders, and 2 for limit orders (from enums we defined above)
    def __str__(self):
        return "Order " + str(self.order) + " executed at price: " + str(self.executionPrice)
