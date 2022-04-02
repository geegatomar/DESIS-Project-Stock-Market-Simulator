from django.shortcuts import render
from trades.models import Trade, Shares_Owned
from django.contrib.auth.decorators import login_required
from stocks.models import Stock


@login_required(login_url='base:login')
def viewTrades(request):
    trades = Trade.objects.filter(user=request.user).order_by('-createdAt')
    print("\n\n\n\n\n\n\n\n In view trades*****\n\n\n\n\n")
    context = {'trades': trades}
    return render(request, 'trades/trades.html', context)


@login_required(login_url='base:login')
def viewUserShares(request):
    stocks_owned = {}
    stocks = Stock.objects.order_by('-currentSharePrice', '-lastTradedAt')
    for stock in stocks:
        stocks_owned[stock.stockName] = []
    shares_owned = Shares_Owned.objects.filter(user=request.user)
    for shares in shares_owned:
        if shares.quantity > 0:
            details = []
            #quantity
            details.append(shares.quantity)
            #Total invested                             
            details.append(shares.quantity*shares.avg_cost_price)
            #total gains       
            details.append(round((shares.stock.currentSharePrice - shares.avg_cost_price)*shares.quantity, 4))
            #profit %age       
            details.append(round((shares.stock.currentSharePrice - shares.avg_cost_price)*100/shares.avg_cost_price, 4))       
            
            stocks_owned[shares.stock.stockName] = details
    context = {'stocks_owned': stocks_owned}
    return render(request, 'trades/shares.html', context)
