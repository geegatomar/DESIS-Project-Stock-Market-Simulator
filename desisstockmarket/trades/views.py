from django.shortcuts import render
from orders.models import OrderDirections
from trades.models import Trade
from django.contrib.auth.decorators import login_required
from stocks.models import Stock


@login_required(login_url='base:login')
def viewTrades(request):
    trades = Trade.objects.filter(user=request.user)
    print("\n\n\n\n\n\n\n\n In view trades*****\n\n\n\n\n")
    context = {'trades': trades}
    return render(request, 'trades/trades.html', context)


@login_required(login_url='base:login')
def viewUserShares(request):
    stocks = Stock.objects.all()
    quantity_stocks_owned = {}
    for stock in stocks:
        quantity_stocks_owned[stock.stockName] = 0
    trades = Trade.objects.filter(user=request.user)
    for trade in trades:
        if trade.order.orderDirection == 'BUY':
            quantity_stocks_owned[trade.order.stock.stockName] += trade.order.quantity
        else:
            quantity_stocks_owned[trade.order.stock.stockName] -= trade.order.quantity
    context = {'quantity_stocks_owned': quantity_stocks_owned}
    return render(request, 'trades/shares.html', context)
