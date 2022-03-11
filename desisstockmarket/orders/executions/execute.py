from stocks.models import Stock
from orders.models import Order, OrderDirections, OrderStatus
from pprint import pprint
from trades.transaction import trade
import time
import threading
from django.contrib.auth import get_user_model
User = get_user_model()

pendingOrders = {}


def initializePendingOrderLists():
    # Read orders initially, whichever are in pending state
    stocks = Stock.objects.all()
    # Initialize a new map of lists for every stock
    # We have 4 types of lists for each stock, two main categories which are buy and sell
    # and each of them are subdivided into market and limit type orders
    for stock in stocks:
        pendingOrders[stock.stockName] = {}
        pendingOrders[stock.stockName]["BUY-MARKET"] = list()
        pendingOrders[stock.stockName]["BUY-LIMIT"] = list()
        pendingOrders[stock.stockName]["SELL-MARKET"] = list()
        pendingOrders[stock.stockName]["SELL-LIMIT"] = list()

    orders = Order.objects.filter(orderStatus=OrderStatus.PENDING)
    for order in orders:
        stockName = order.stock.stockName
        orderDirection = order.orderDirection
        orderType = order.orderType
        typeOfList = str(orderDirection + "-" + orderType)
        pendingOrders[stockName][typeOfList].append(order)

    # Sorting by specific order specified for each of the four lists
    for stock in stocks:
        pendingOrders[stock.stockName]["BUY-MARKET"].sort(
            key=lambda x: x.createdAt)
        pendingOrders[stock.stockName]["SELL-MARKET"].sort(
            key=lambda x: x.createdAt)
        # Buy limit orders shall have those willing to buy at the highest price first
        pendingOrders[stock.stockName]["BUY-LIMIT"].sort(
            key=lambda x: x.limitPrice, reverse=True)
        # Sell limit orders shall have those willing to sell at lower prices first
        pendingOrders[stock.stockName]["SELL-LIMIT"].sort(
            key=lambda x: x.limitPrice)

# Takes as input a list of orders, and eliminates all executed orders, returning only the pending orders


def removeExecutedOrders(orders):
    updatedPendingOrder = []
    for order in orders:
        if order.orderStatus not in ('OrderStatus.EXECUTED', 'EXECUTED', OrderStatus.EXECUTED):
            updatedPendingOrder.append(order)
        else:
            print("\n\nITS AN EXECUTED ORDER. REMOVING IT\n\n ")
    return updatedPendingOrder


def sendExecutedOrdersToTrades(executed_orders_and_price):
    for execution in executed_orders_and_price:
        print("\n\n\n--------------Inside sendExecutedOrdersToTrades---------------\n\n")

        order = execution[0]
        price = execution[1]
        trade.addNewTrade(order, price)
        # Also reduce or increase the account balance for the particular user
        current_account_value = order.user.account_value

        if order.orderDirection == 'BUY':
            User.objects.filter(id=order.user.id).update(
                account_value=current_account_value - price)
            #order.user.account_value -= price
        else:
            User.objects.filter(id=order.user.id).update(
                account_value=current_account_value + price)
            #order.user.account_value += price

# TODO: Make sure to add check that transaction shall not be withing same user


def executeBuyMarketOrders(stock, buy_market_orders, sell_market_orders, sell_limit_orders):
    currentSharePrice = stock.currentSharePrice
    executed_orders_and_price = []
    # Matching buy market orders with sell market orders
    for i, buy_order in enumerate(buy_market_orders):
        # First we match against other market sell orders
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        for j, sell_order in enumerate(sell_market_orders):
            if sell_order.user == buy_order.user:
                continue
            available_to_buy += sell_order.dynamicQuantity
            if available_to_buy >= wants_to_buy:
                index = j
                break
        print("++++++++++++================= ")
        print("wants_to_buy", wants_to_buy)
        print("available_to_buy:", available_to_buy)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible b/w market orders of buy and sell
            continue

        Order.objects.filter(id=buy_market_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0)
        buy_market_orders[i].orderStatus = OrderStatus.EXECUTED
        executed_orders_and_price.append(
            (buy_market_orders[i], currentSharePrice))
        quantity_so_far = 0
        for j in range(index + 1):
            if sell_market_orders[j].user == buy_order.user:
                continue
            quantity_so_far += sell_market_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_buy:
                # Then full order get executed, and updates status
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0)
                sell_market_orders[j].orderStatus = OrderStatus.EXECUTED
                sell_market_orders[j].dynamicQuantity = 0
                executed_orders_and_price.append(
                    (sell_market_orders[i], currentSharePrice))
            else:
                # Then partial execution, and status remains as pending
                sell_market_orders[j].dynamicQuantity = (
                    quantity_so_far - wants_to_buy)
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.PENDING, dynamicQuantity=quantity_so_far - wants_to_buy)

        print("executed_orders_and_price: ", executed_orders_and_price)
        sell_market_orders = removeExecutedOrders(sell_market_orders)

    buy_market_orders = removeExecutedOrders(buy_market_orders)

    # TODO: Matching buy market orders with sell limit orders
    for i, buy_order in enumerate(buy_market_orders):
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        # First check if its possible, i.e. if there are enough sellers to accomodate for this buyer
        for j, sell_order in enumerate(sell_limit_orders):
            if sell_order.user == buy_order.user:
                continue
            # TODO: The logic here is that if there are enough sellers to sell, then each transaction happens at half of the price b/w the currentSharePrice and limitPrice
            pass

        # TODO: Update the market price if limit order transactions occurs

    # Send all these executed orders along with the price at which they were executed
    sendExecutedOrdersToTrades(executed_orders_and_price)
    return buy_market_orders, sell_market_orders, sell_limit_orders


def executeBuyLimitOrders(stock, buy_limit_orders, sell_market_orders, sell_limit_orders):
    # TODO
    return buy_limit_orders, sell_market_orders, sell_limit_orders


def executeSellMarketOrders(stock, sell_market_orders, buy_market_orders, buy_limit_orders):
    # TODO
    return sell_market_orders, buy_market_orders, buy_limit_orders


def executeSellLimitOrders(stock, sell_limit_orders, buy_market_orders, buy_limit_orders):
    # TODO
    return sell_limit_orders, buy_market_orders, buy_limit_orders


def executeOrder(stockName, orderLists):
    print("Executing orders for: ", stockName)
    stock = Stock.objects.get(stockName=stockName)
    currentSharePrice = stock.currentSharePrice

    buy_market_orders = orderLists["BUY-MARKET"]
    buy_limit_orders = orderLists["BUY-LIMIT"]
    sell_market_orders = orderLists["SELL-MARKET"]
    sell_limit_orders = orderLists["SELL-LIMIT"]

    buy_market_orders, sell_market_orders, sell_limit_orders = executeBuyMarketOrders(stock, buy_market_orders,
                                                                                      sell_market_orders, sell_limit_orders)
    buy_limit_orders, sell_market_orders, sell_limit_orders = executeBuyLimitOrders(stock, buy_limit_orders,
                                                                                    sell_market_orders, sell_limit_orders)
    sell_market_orders, buy_market_orders, buy_limit_orders = executeSellMarketOrders(stock, sell_market_orders,
                                                                                      buy_market_orders, buy_limit_orders)
    sell_limit_orders, buy_market_orders, buy_limit_orders = executeSellLimitOrders(stock, sell_limit_orders,
                                                                                    buy_market_orders, buy_limit_orders)
    orderLists["BUY-MARKET"] = buy_market_orders
    orderLists["BUY-LIMIT"] = buy_limit_orders
    orderLists["SELL-MARKET"] = sell_market_orders
    orderLists["SELL-LIMIT"] = sell_limit_orders

    print("Exiting execute orders.............................")
    return orderLists
    # TODO: Update the market price if limit order transactions occur inside of each function
    pass


def mainExecutor():
    # Picking up all pending orders from the DB
    initializePendingOrderLists()

    while True:
        # Executing orders for each stock individually
        for stock in pendingOrders:
            updatedOrderLists = executeOrder(stock, pendingOrders[stock])
            pendingOrders[stock] = updatedOrderLists

        # TODO: Change the sleep time to few miliseconds after development and testing it done
        print("-----------------------------------------------------------before sleeping-----")
        time.sleep(5)
        print("------------------------------------------------------------after sleeping-----")

        print("######################################111111111")
        pprint(pendingOrders)
        print("######################################222222222")
