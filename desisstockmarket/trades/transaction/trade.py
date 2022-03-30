import decimal
from trades.models import Trade, Shares_Owned
# Create your views here.


def addNewTrade(order, price):
    profit = 0.0
    if order.orderDirection == "SELL":
        cost_price = Shares_Owned.objects.filter(user=order.user, stock=order.stock)[0].avg_cost_price
        profit = decimal.Decimal(100.0)*(price - cost_price)/cost_price
    trade = Trade(order=order, executionPrice=price, user=order.user, profit=profit)
    trade.save()
