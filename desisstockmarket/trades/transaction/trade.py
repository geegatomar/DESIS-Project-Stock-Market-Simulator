from trades.models import Trade
# Create your views here.


def addNewTrade(order, price):
    trade = Trade(order=order, executionPrice=price, user=order.user)
    trade.save()
