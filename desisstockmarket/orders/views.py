from email import message
from pickle import FALSE, TRUE
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from .models import Order, OrderDirections
from .forms import OrderForm
from stocks.models import Stock
from trades.models import Trade, Shares_Owned
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from orders.executions import execute
import pprint
# from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your views here.

# Home page of stocks displays list of all stocks that are available and can be traded
# on our platform.

# Home page shall show you all the orders by this user
# TODO: Change it for particular user after adding user


@login_required(login_url='base:login')
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # TODO: Maybe Later we shall filter out only the top 10 or so stocks to show here in home of orders
    stocks = Stock.objects.all()
    orders = Order.objects.filter(
        Q(user=request.user) &
        (Q(stock__stockName__icontains=q) |
         Q(stock__fullCompanyName__icontains=q)))

    orders_count = orders.count()
    context = {'orders': orders, 'stocks': stocks,
               'orders_count': orders_count}
    return render(request, 'orders/home.html', context)


def isValidTransaction(order):
    # TODO - DONE: Add condition for selling later
    # if order.orderDirection == OrderDirections.SELL:
    #     return True, ""
    ''''
    if order.orderDirection == 'SELL':
        if Shares_Owned.objects.filter(user=order.user, stock=order.stock).exists():
            currently_owned = Shares_Owned.objects.filter(user=order.user, stock=order.stock)[0].quantity
            if(currently_owned < order.quantity):
                return False, "Insufficient shares to sell! You cannot sell stocks that you don\'t own."
        else:
            return False, "Insufficient shares to sell! You cannot sell stocks that you don\'t own."
    '''

    if order.orderDirection == 'BUY':
        share_price = order.limitPrice
        account_value = order.user.account_value

        if share_price * order.quantity > account_value:
            return False, 'Insufficient balance to buy stock'
    
    if order.quantity < 1:      # Add upper limit as well
        return False, "Invalid Quantity!"
    
    if order.limitPrice <= 0:
        return False, "Invalid Limit Price!"
    
    # You cannot buy more than the outstanding number of shares
    if order.quantity > order.stock.sharesOutstanding:
        return False, 'You cannot buy more than the outstanding number of shares'
    
    # Rate Limiter
    bulk_orders = Order.objects.filter(
        Q(user=order.user) & Q(stock=order.stock) & Q(orderDirection="BUY"))
    
    print(bulk_orders)
    print()
    print(bulk_orders.count())
    if bulk_orders.count() > 5:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print(timezone.now())
        print(bulk_orders[5].createdAt)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        elapsedTime = timezone.now() - bulk_orders[5].createdAt
        if elapsedTime.total_seconds() < 10*60:
            return False, 'Rate Limitation! Can\'t make more than 5 orders in 10 minutes.'
    
    return True, ""

# TODO: Not sure how we will support Edit and Delete order functionality now... need to probably remove it

# Inserts an element in a sorted list such that final list is also sorted
# We are using this for sorted sell orders such that lease price is at front


def insertSuchThatSortedAscending(orders, order_to_insert):
    inserted = False
    for i, ord in enumerate(orders):
        if ord.limitPrice > order_to_insert.limitPrice:
            orders.insert(i, order_to_insert)
            inserted = True
            break
    if not inserted:
        orders.append(order_to_insert)
    return orders

# Inserts an element in a sorted list such that final list is also sorted
# We are using this for sorted buy orders such that highest price is at front


def insertSuchThatSortedDescending(orders, order_to_insert):
    inserted = False
    for i, ord in enumerate(orders):
        if ord.limitPrice < order_to_insert.limitPrice:
            orders.insert(i, order_to_insert)
            inserted = True
            break
    if not inserted:
        orders.append(order_to_insert)
    return orders


def addOrderToExecutionList(order):
    print("\n\n\n************ Adding order: \n\n")
    print(order.orderStatus)
    stockName = order.stock.stockName
    orderDirection = order.orderDirection
    orderType = order.orderType
    typeOfList = str(orderDirection + "-" + orderType)
    # TODO: Currently I'm just appending, but I need to make sure they are in a
    # certain sorted order by date or by price, according to which queue/list it is
    if typeOfList == "BUY-MARKET" or typeOfList == "SELL-MARKET":
        execute.pendingOrders[stockName][typeOfList].append(order)
    elif typeOfList == "BUY-LIMIT":
        # Buy limit orders shall have max buy price in front
        execute.pendingOrders[stockName][typeOfList] = insertSuchThatSortedDescending(
            execute.pendingOrders[stockName][typeOfList], order)
    else:
        execute.pendingOrders[stockName][typeOfList] = insertSuchThatSortedAscending(
            execute.pendingOrders[stockName][typeOfList], order)

    print("-----------------------------------")
    print(execute.pendingOrders)


@login_required(login_url='base:login')
def createOrderWithInitialData(request, pk, direction):
    stock = Stock.objects.get(stockId=pk)

    initial_dict = {
        'stock': stock,
        'orderDirection': direction,
    }
    form = OrderForm(initial=initial_dict)
    if request.method == "POST":
        # print(request.POST)
        form = OrderForm(request.POST)
        if form.is_valid():
            # If the data received via the form is valid, we save it to the DB
            order = form.save(commit=False)
            order.user = request.user
            order.dynamicQuantity = order.quantity
            order.quantityExecuted = 0
            if order.orderType == "MARKET" or order.limitPrice is None:
                order.limitPrice = order.stock.currentSharePrice
            
            # TODO - DONE: Probably later also add a check that you cannot sell stocks that you don't own yet
            isvalid, err = isValidTransaction(order)
            if isvalid:
                order.save()
                addOrderToExecutionList(order)
                # After form has been saved, we just redirect back to home page
                return redirect('orders:home')
            else:
                messages.error(request, err)
    context = {"form": form}
    return render(request, 'orders/order_form.html', context)


@login_required(login_url='base:login')
def createOrder(request):
    form = OrderForm()

    # Post route is hit after user has submitted their details
    if request.method == "POST":
        # print(request.POST)
        form = OrderForm(request.POST)
        if form.is_valid():
            # If the data received via the form is valid, we save it to the DB
            order = form.save(commit=False)
            order.user = request.user
            order.dynamicQuantity = order.quantity
            order.quantityExecuted = 0
            if order.orderType == "MARKET" or order.limitPrice is None:
                order.limitPrice = order.stock.currentSharePrice
            # TODO - DONE: Probably later also add a check that you cannot sell stocks that you don't own yet
            
            isvalid, err = isValidTransaction(order)
            if isvalid:
                order.save()
                addOrderToExecutionList(order)
                # After form has been saved, we just redirect back to home page
                return redirect('orders:home')
            else:
                messages.error(request, err)

    context = {"form": form}
    return render(request, 'orders/order_form.html', context)

# TODO: Not sure how we will support Edit and Delete order functionality now... need to probably remove it
# TODO: I think we should remove the edit and delete functionality for orders completely...

# Removing this functionality
'''
@login_required(login_url='base:login')
def updateOrder(request, pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            #order.updatedAt = datetime.now()
            #order.updatedAt = timezone.now()
            order.updatedAt = datetime.datetime.now()
            order.dynamicQuantity = order.quantity
            order.quantityExecuted = 0
            if order.orderType == "MARKET" or order.limitPrice is None:
                order.limitPrice = order.stock.currentSharePrice
            
            # TODO - DONE: The sorting of orders isn't working correctly. If I update an order
            # then it should come on the top of the list, which isnt happening currently.

            # order.save(update_fields=['updatedAt'])
            # order.save()
            # return redirect('orders:home')

            isvalid, err = isValidTransaction(order)
            if isvalid:
                order.save()
                return redirect('orders:home')
            else:
                messages.error(request, err)

    context = {'form': form}
    return render(request, 'orders/order_form.html', context)


@login_required(login_url='base:login')
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)

    # If its a POST request, means that the user submitted the form, and hence we shall delete
    if request.method == "POST":
        order.delete()
        return redirect('orders:home')

    context = {'obj': order}
    return render(request, 'orders/delete.html', context)
'''