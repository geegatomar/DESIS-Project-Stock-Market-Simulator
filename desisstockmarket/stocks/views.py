from django.shortcuts import render
from django.http import HttpResponse
from stocks.models import Stock

# Create your views here.

# Home page of stocks displays list of all stocks that are available and can be traded
# on our platform.


def home(request):
    #stocks = Stock.objects.all()
    stocks = Stock.objects.order_by('-currentSharePrice', '-lastTradedAt')
    context = {'stocks': stocks}
    return render(request, 'stocks/home.html', context)

# Info about each individual stock


def info(request, id):
    stock = Stock.objects.get(stockId=id)
    context = {'stock': stock}
    return render(request, 'stocks/info.html', context)
