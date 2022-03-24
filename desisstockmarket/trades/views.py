from django.shortcuts import render
from orders.models import OrderDirections
from trades.models import Trade, Shares_Owned
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
    '''
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
    '''
    stocks_owned = {}
    stocks = Stock.objects.all()
    for stock in stocks:
        stocks_owned[stock.stockName] = []
    shares_owned = Shares_Owned.objects.filter(user=request.user)
    for shares in shares_owned:
        details = []
        #quantity
        details.append(shares.quantity)
        #Total invested                             
        details.append(shares.quantity*shares.avg_cost_price)
        #total gains       
        details.append((shares.stock.currentSharePrice - shares.avg_cost_price)*shares.quantity)
        #profit %age       
        details.append((shares.stock.currentSharePrice - shares.avg_cost_price)*100/shares.avg_cost_price)       
        
        stocks_owned[shares.stock.stockName] = details
        print("$$$$$$$$$$$$$$ PRINTING $$$$$$$$$$$")
        print(stocks_owned[shares.stock.stockName])
    context = {'stocks_owned': stocks_owned}
    return render(request, 'trades/shares.html', context)
