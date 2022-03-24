from stocks.models import Stock, StockPriceHistory
from orders.models import Order, OrderDirections, OrderStatus
from trades.models import Shares_Owned
from pprint import pprint
from trades.transaction import trade
import time
import threading
from django.utils import timezone
from django.db.models import Q
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

    orders = Order.objects.filter(Q(orderStatus=OrderStatus.PENDING) | Q(orderStatus=OrderStatus.PARTIAL))
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
                account_value=current_account_value - price * (order.quantity - order.dynamicQuantity - order.quantityExecuted))
            #order.user.account_value -= price
            #Order.objects.filter(id=order.id).update(quantityExecuted=order.quantity - order.dynamicQuantity)
        else:
            User.objects.filter(id=order.user.id).update(
                account_value=current_account_value + price * (order.quantity - order.dynamicQuantity - order.quantityExecuted))
            #order.user.account_value += price
            #Order.objects.filter(id=order.id).update(quantityExecuted=order.quantity - order.dynamicQuantity)

# TODO - DONE: Make sure to add check that transaction shall not be withing same user

# Update in Shares_Owned
def updateSharesOwnedForBuyOrder(order, cost_price):
    bought_quantity = order.quantity - order.dynamicQuantity - order.quantityExecuted
    if Shares_Owned.objects.filter(user=order.user, stock=order.stock).exists():
        current_shares = Shares_Owned.objects.filter(user=order.user, stock=order.stock)
        current_quantity = current_shares[0].quantity
        current_cp = current_shares[0].avg_cost_price
        new_quantity = current_quantity + bought_quantity
        new_cp = (current_cp*current_quantity + cost_price*bought_quantity) / new_quantity

        Shares_Owned.objects.filter(user=order.user, stock=order.stock).update(
                    quantity=new_quantity, avg_cost_price=new_cp)
    else:
        # Create new entry
        new_share_rec = Shares_Owned(user=order.user, stock=order.stock, quantity=bought_quantity, avg_cost_price=cost_price)
        new_share_rec.save()
    
    print("Sucessfully executed <<< updateSharesOwnedForBuyOrder() >>>")

# Update in Shares_Owned
def updateSharesOwnedForSellOrder(order):
    if Shares_Owned.objects.filter(user=order.user, stock=order.stock).exists():
        sold_quantity = order.quantity - order.dynamicQuantity - order.quantityExecuted
        current_shares = Shares_Owned.objects.filter(user=order.user, stock=order.stock)
        current_quantity = current_shares[0].quantity

        Shares_Owned.objects.filter(user=order.user, stock=order.stock).update(
                    quantity=(current_quantity - sold_quantity))
    
    print("Sucessfully executed <<< updateSharesOwnedForSellOrder() >>>")

def isValidTransaction(order):
    ''''
    if order.orderDirection == 'SELL':
        if Shares_Owned.objects.filter(user=order.user, stock=order.stock).exists():
            currently_owned = Shares_Owned.objects.filter(user=order.user, stock=order.stock)[0].quantity
            if(currently_owned < order.quantity):
                return False, "Insufficient shares to sell! You cannot sell stocks that you don\'t own."
        else:
            return False
    '''
    
    if order.orderDirection == 'BUY':
        share_price = order.limitPrice
        account_value = order.user.account_value

        if share_price * (order.quantity - order.dynamicQuantity - order.quantityExecuted) > account_value:
            return False
    
    return True

def executeBuyMarketOrders(stock, buy_market_orders, sell_market_orders, sell_limit_orders):
    currentSharePrice = stock.currentSharePrice
    executed_orders_and_price = []
    # Matching buy market orders with sell market orders
    for i, buy_order in enumerate(buy_market_orders):
        if not isValidTransaction(buy_order):
            continue
        # First we match against other market sell orders
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        for j, sell_order in enumerate(sell_market_orders):
            if sell_order.user == buy_order.user or (not isValidTransaction(sell_order)):
                continue
            available_to_buy += sell_order.dynamicQuantity
            if available_to_buy >= wants_to_buy:
                index = j
                break
        print("++++++++++++================= ")
        print("Stock: ", buy_order.stock.stockName)
        print("User: ", buy_order.user.USERNAME_FIELD)
        print("Buy Market - Sell Market")
        print("wants_to_buy", wants_to_buy)
        print("available_to_buy:", available_to_buy)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible b/w market orders of buy and sell
            continue

        Stock.objects.filter(stockId=buy_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        for j in range(index + 1):
            if sell_market_orders[j].user == buy_order.user or (not isValidTransaction(sell_market_orders[j])):
                continue
            quantity_so_far += sell_market_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_buy:
                # Then full order get executed, and updates status
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_market_orders[j].quantity)
                sell_market_orders[j].orderStatus = OrderStatus.EXECUTED
                sell_market_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_market_orders[j])

                executed_orders_and_price.append(
                    (sell_market_orders[j], currentSharePrice))
                
                sell_market_orders[j].quantityExecuted = sell_market_orders[j].quantity
            else:
                # Then partial execution, and status remains as pending
                sell_market_orders[j].dynamicQuantity = (quantity_so_far - wants_to_buy)
                sell_market_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=sell_market_orders[j].dynamicQuantity,
                    quantityExecuted=sell_market_orders[j].quantity - sell_market_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_market_orders[j])

                executed_orders_and_price.append(           # Contains Partially executed as well
                    (sell_market_orders[j], currentSharePrice))
                
                sell_market_orders[j].quantityExecuted = sell_market_orders[j].quantity - sell_market_orders[j].dynamicQuantity

        Order.objects.filter(id=buy_market_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_market_orders[i].quantity)
        buy_market_orders[i].orderStatus = OrderStatus.EXECUTED
        buy_market_orders[i].dynamicQuantity = 0
        # Update in Shares_Owned
        updateSharesOwnedForBuyOrder(buy_market_orders[i], currentSharePrice)
        
        executed_orders_and_price.append(
            (buy_market_orders[i], currentSharePrice))

        buy_market_orders[i].quantityExecuted = buy_market_orders[i].quantity

        print("executed_orders_and_price: ", executed_orders_and_price)
        sell_market_orders = removeExecutedOrders(sell_market_orders)

    buy_market_orders = removeExecutedOrders(buy_market_orders)

    # TODO - DONE: Matching buy market orders with sell limit orders
    for i, buy_order in enumerate(buy_market_orders):
        if not isValidTransaction(buy_order):
            continue
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        # First check if its possible, i.e. if there are enough sellers to accomodate for this buyer
        for j, sell_order in enumerate(sell_limit_orders):
            if sell_order.user == buy_order.user or sell_order.limitPrice > currentSharePrice or (not isValidTransaction(sell_order)):      #<<<< added condition >>>>
                continue
            # TODO - DONE: The logic here is that if there are enough sellers to sell, then each transaction happens at half of the price b/w the currentSharePrice and limitPrice
            #pass
    ##################################<<<< DONE >>>>###################################################################
            available_to_buy += sell_order.dynamicQuantity
            if available_to_buy >= wants_to_buy:
                index = j
                break
        
        print("++++++++++++================= ")
        print("Stock: ", buy_order.stock.stockName)
        print("User: ", buy_order.user.USERNAME_FIELD)
        print("Buy Market - Sell Limit")
        print("wants_to_buy", wants_to_buy)
        print("available_to_buy:", available_to_buy)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue

        Stock.objects.filter(stockId=buy_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        total_cost = 0
        for j in range(index + 1):
            if sell_limit_orders[j].user == buy_order.user or sell_limit_orders[j].limitPrice > currentSharePrice or (not isValidTransaction(sell_limit_orders[j])):
                continue
            quantity_so_far += sell_limit_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_buy:
                # Then full order get executed, and updates status
                total_cost = sell_limit_orders[j].dynamicQuantity * (currentSharePrice + sell_limit_orders[j].limitPrice)/2

                Order.objects.filter(id=sell_limit_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_limit_orders[j].quantity)
                sell_limit_orders[j].orderStatus = OrderStatus.EXECUTED
                sell_limit_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_limit_orders[j])

                executed_orders_and_price.append(
                    (sell_limit_orders[j], (currentSharePrice + sell_limit_orders[j].limitPrice)/2))
            else:
                # Then partial execution, and status remains as pending
                total_cost = (sell_limit_orders[j].dynamicQuantity - (quantity_so_far - wants_to_buy)) * (currentSharePrice + sell_limit_orders[j].limitPrice)/2

                sell_limit_orders[j].dynamicQuantity = (quantity_so_far - wants_to_buy)
                sell_limit_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=sell_limit_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=quantity_so_far - wants_to_buy, 
                    quantityExecuted=sell_limit_orders[j].quantity - sell_limit_orders[j].dynamicQuantity)

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_limit_orders[j])
                
                # MAYBE
                executed_orders_and_price.append(
                    (sell_limit_orders[j], (currentSharePrice + sell_limit_orders[j].limitPrice)/2))
        
        Order.objects.filter(id=buy_market_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_market_orders[i].quantity)
        buy_market_orders[i].orderStatus = OrderStatus.EXECUTED
        buy_market_orders[i].dynamicQuantity = 0
        new_price = total_cost/wants_to_buy
        
        # Update in Shares_Owned
        updateSharesOwnedForBuyOrder(buy_market_orders[i], new_price)

        executed_orders_and_price.append(
            (buy_market_orders[i], new_price))
        
        print("executed_orders_and_price: ", executed_orders_and_price)
        sell_limit_orders = removeExecutedOrders(sell_limit_orders)

        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # TODO: how to determine the new price?
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        currentSharePrice = new_price

        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

    buy_market_orders = removeExecutedOrders(buy_market_orders)
    ##################################<<<< DONE >>>>###################################################################

        # TODO - DONE: Update the market price if limit order transactions occurs
        # DONE AFTER EXECUTION OF EACH BUY-MARKET ORDER - LINE 203

    # Send all these executed orders along with the price at which they were executed
    sendExecutedOrdersToTrades(executed_orders_and_price)
    return buy_market_orders, sell_market_orders, sell_limit_orders


def executeBuyLimitOrders(stock, buy_limit_orders, sell_market_orders, sell_limit_orders):
    # TODO - DONE
    executed_orders_and_price = []
    # Matching buy limit orders with sell market orders
    for i, buy_order in enumerate(buy_limit_orders):
        if not isValidTransaction(buy_order):
            continue
        # First we match against other market sell orders
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        currentSharePrice = stock.currentSharePrice
        for j, sell_order in enumerate(sell_market_orders):
            if sell_order.user == buy_order.user or currentSharePrice > buy_order.limitPrice or (not isValidTransaction(sell_order)):
                continue
            available_to_buy += sell_order.dynamicQuantity
            if available_to_buy >= wants_to_buy:
                index = j
                break
        print("++++++++++++================= ")
        print("Stock: ", buy_order.stock.stockName)
        print("User: ", buy_order.user.USERNAME_FIELD)
        print("Buy Limit - Sell Market")
        print("wants_to_buy", wants_to_buy)
        print("available_to_buy:", available_to_buy)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue
        
        Stock.objects.filter(stockId=buy_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        for j in range(index + 1):
            if sell_market_orders[j].user == buy_order.user or currentSharePrice > buy_order.limitPrice or (not isValidTransaction(sell_market_orders[j])):
                continue
            quantity_so_far += sell_market_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_buy:
                total_cost = sell_market_orders[j].dynamicQuantity * (currentSharePrice + buy_order.limitPrice)/2
                # Then full order get executed, and updates status
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_market_orders[j].quantity)
                sell_market_orders[j].orderStatus = OrderStatus.EXECUTED
                sell_market_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_market_orders[j])
                
                executed_orders_and_price.append(
                    (sell_market_orders[j], (currentSharePrice + buy_order.limitPrice)/2))
                
                sell_market_orders[j].quantityExecuted = sell_market_orders[j].quantity
                
            else:
                total_cost = (sell_market_orders[j].dynamicQuantity - (quantity_so_far - wants_to_buy)) * (currentSharePrice + buy_order.limitPrice)/2
                # Then partial execution, and status remains as pending
                sell_market_orders[j].dynamicQuantity = (quantity_so_far - wants_to_buy)
                sell_market_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=sell_market_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=sell_market_orders[j].dynamicQuantity, 
                    quantityExecuted=sell_market_orders[j].quantity - sell_market_orders[j].dynamicQuantity)

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_market_orders[j])

                # MAYBE
                executed_orders_and_price.append(
                    (sell_market_orders[j], (currentSharePrice + buy_order.limitPrice)/2))
                
                sell_market_orders[j].quantityExecuted = sell_market_orders[j].quantity - sell_market_orders[j].dynamicQuantity

        Order.objects.filter(id=buy_limit_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_limit_orders[i].quantity)
        buy_limit_orders[i].orderStatus = OrderStatus.EXECUTED
        buy_limit_orders[i].dynamicQuantity = 0

        new_price = total_cost/wants_to_buy

        # Update in Shares_Owned
        updateSharesOwnedForBuyOrder(buy_limit_orders[i], new_price)

        executed_orders_and_price.append(
            (buy_limit_orders[i], new_price))

        buy_limit_orders[i].quantityExecuted = buy_limit_orders[i].quantity
        
        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # MAYBE id=stock.id
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        #currentSharePrice = new_price
        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

        print("executed_orders_and_price: ", executed_orders_and_price)
        sell_market_orders = removeExecutedOrders(sell_market_orders)

    buy_limit_orders = removeExecutedOrders(buy_limit_orders)

    # Matching buy limit orders with sell limit orders
    for i, buy_order in enumerate(buy_limit_orders):
        if not isValidTransaction(buy_order):
            continue
        wants_to_buy = buy_order.dynamicQuantity
        available_to_buy = 0
        index = -1
        # First check if its possible, i.e. if there are enough sellers to accomodate for this buyer
        for j, sell_order in enumerate(sell_limit_orders):
            if sell_order.user == buy_order.user or sell_order.limitPrice > buy_order.limitPrice or (not isValidTransaction(sell_order)):
                continue
            available_to_buy += sell_order.dynamicQuantity
            if available_to_buy >= wants_to_buy:
                index = j
                break
        
        print("++++++++++++================= ")
        print("Stock: ", buy_order.stock.stockName)
        print("User: ", buy_order.user.USERNAME_FIELD)
        print("Buy Limit - Sell Limit")
        print("wants_to_buy", wants_to_buy)
        print("available_to_buy:", available_to_buy)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue

        Stock.objects.filter(stockId=buy_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        total_cost = 0
        for j in range(index + 1):
            if sell_limit_orders[j].user == buy_order.user or sell_limit_orders[j].limitPrice > buy_order.limitPrice or (not isValidTransaction(sell_limit_orders[j])):
                continue
            quantity_so_far += sell_limit_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_buy:
                total_cost = sell_limit_orders[j].dynamicQuantity * (buy_order.limitPrice + sell_limit_orders[j].limitPrice)/2
                # Then full order get executed, and updates status
                Order.objects.filter(id=sell_limit_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_limit_orders[j].quantity)
                sell_limit_orders[j].orderStatus = OrderStatus.EXECUTED
                sell_limit_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_limit_orders[j])

                executed_orders_and_price.append(
                    (sell_limit_orders[j], (buy_order.limitPrice + sell_limit_orders[j].limitPrice)/2))
                
                sell_limit_orders[j].quantityExecuted = sell_limit_orders[j].quantity
            else:
                total_cost = (sell_limit_orders[j].dynamicQuantity - (quantity_so_far - wants_to_buy)) * (buy_order.limitPrice + sell_limit_orders[j].limitPrice)/2
                # Then partial execution, and status remains as pending
                sell_limit_orders[j].dynamicQuantity = (quantity_so_far - wants_to_buy)
                sell_limit_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=sell_limit_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=sell_limit_orders[j].dynamicQuantity, 
                    quantityExecuted=sell_limit_orders[j].quantity - sell_limit_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForSellOrder(sell_limit_orders[j])

                # MAYBE
                executed_orders_and_price.append(
                    (sell_limit_orders[j], (buy_order.limitPrice + sell_limit_orders[j].limitPrice)/2))
                
                sell_limit_orders[j].quantityExecuted = sell_limit_orders[j].quantity - sell_limit_orders[j].dynamicQuantity
        
        Order.objects.filter(id=buy_limit_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_limit_orders[i].quantity)
        buy_limit_orders[i].orderStatus = OrderStatus.EXECUTED
        buy_limit_orders[i].dynamicQuantity = 0
        
        new_price = total_cost/wants_to_buy

        # Update in Shares_Owned
        updateSharesOwnedForBuyOrder(buy_limit_orders[i], new_price)

        executed_orders_and_price.append(
            (buy_limit_orders[i], new_price))
        
        buy_limit_orders[i].quantityExecuted = buy_limit_orders[i].quantity
        
        print("executed_orders_and_price: ", executed_orders_and_price)
        sell_limit_orders = removeExecutedOrders(sell_limit_orders)

        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # MAYBE id=stock.id
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        #currentSharePrice = new_price
        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

    buy_limit_orders = removeExecutedOrders(buy_limit_orders)
    
    # Send all these executed orders along with the price at which they were executed
    sendExecutedOrdersToTrades(executed_orders_and_price)
    return buy_limit_orders, sell_market_orders, sell_limit_orders


def executeSellMarketOrders(stock, sell_market_orders, buy_market_orders, buy_limit_orders):
    # TODO - DONE
    currentSharePrice = stock.currentSharePrice
    executed_orders_and_price = []
    # Matching sell market orders with buy market orders
    for i, sell_order in enumerate(sell_market_orders):
        if not isValidTransaction(sell_order):
            continue
        # First we match against other market buy orders
        wants_to_sell = sell_order.dynamicQuantity
        available_to_sell = 0
        index = -1
        for j, buy_order in enumerate(buy_market_orders):
            if buy_order.user == sell_order.user or (not isValidTransaction(buy_order)):
                continue
            available_to_sell += buy_order.dynamicQuantity
            if available_to_sell >= wants_to_sell:
                index = j
                break
        print("++++++++++++================= ")
        print("Stock: ", sell_order.stock.stockName)
        print("User: ", sell_order.user.USERNAME_FIELD)
        print("Sell Market - Sell Market")
        print("wants_to_sell", wants_to_sell)
        print("available_to_sell:", available_to_sell)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue

        Stock.objects.filter(stockId=sell_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        for j in range(index + 1):
            if buy_market_orders[j].user == sell_order.user or (not isValidTransaction(buy_market_orders[j])):
                continue
            quantity_so_far += buy_market_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_sell:
                # Then full order get executed, and updates status
                Order.objects.filter(id=buy_market_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_market_orders[j].quantity)
                buy_market_orders[j].orderStatus = OrderStatus.EXECUTED
                buy_market_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_market_orders[j], currentSharePrice)

                executed_orders_and_price.append(
                    (buy_market_orders[j], currentSharePrice))
                
                buy_market_orders[j].quantityExecuted = buy_market_orders[j].quantity
            else:
                # Then partial execution, and status remains as pending
                buy_market_orders[j].dynamicQuantity = (quantity_so_far - wants_to_sell)
                buy_market_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=buy_market_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=buy_market_orders[j].dynamicQuantity, 
                    quantityExecuted=buy_market_orders[j].quantity - buy_market_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_market_orders[j], currentSharePrice)

                executed_orders_and_price.append(
                    (buy_market_orders[j], currentSharePrice))
                
                buy_market_orders[j].quantityExecuted = buy_market_orders[j].quantity

        Order.objects.filter(id=sell_market_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_market_orders[i].quantity)
        sell_market_orders[i].orderStatus = OrderStatus.EXECUTED
        sell_market_orders[i].dynamicQuantity = 0

        # Update in Shares_Owned
        updateSharesOwnedForSellOrder(sell_market_orders[i])

        executed_orders_and_price.append(
            (sell_market_orders[i], currentSharePrice))
        
        sell_market_orders[i].quantityExecuted = sell_market_orders[i].quantity
        
        print("executed_orders_and_price: ", executed_orders_and_price)
        buy_market_orders = removeExecutedOrders(buy_market_orders)

    sell_market_orders = removeExecutedOrders(sell_market_orders)

    # Matching sell market orders with buy limit orders
    for i, sell_order in enumerate(sell_market_orders):
        if not isValidTransaction(sell_order):
            continue
        wants_to_sell = sell_order.dynamicQuantity
        available_to_sell = 0
        index = -1
        # First check if its possible, i.e. if there are enough buyers to accomodate for this seller
        for j, buy_order in enumerate(buy_limit_orders):
            if buy_order.user == sell_order.user or buy_order.limitPrice < currentSharePrice or (not isValidTransaction(buy_order)):
                continue

            available_to_sell += buy_order.dynamicQuantity
            if available_to_sell >= wants_to_sell:
                index = j
                break
        
        print("++++++++++++================= ")
        print("Stock: ", sell_order.stock.stockName)
        print("User: ", sell_order.user.USERNAME_FIELD)
        print("Sell Market - Buy Limit")
        print("wants_to_sell", wants_to_sell)
        print("available_to_sell:", available_to_sell)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue

        Stock.objects.filter(stockId=sell_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        total_cost = 0
        for j in range(index + 1):
            if buy_limit_orders[j].user == sell_order.user or buy_limit_orders[j].limitPrice < currentSharePrice or (not isValidTransaction(buy_limit_orders[j])):
                continue
            quantity_so_far += buy_limit_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_sell:
                total_cost = buy_limit_orders[j].dynamicQuantity * (currentSharePrice + buy_limit_orders[j].limitPrice)/2
                # Then full order get executed, and updates status
                Order.objects.filter(id=buy_limit_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_limit_orders[j].quantity)
                buy_limit_orders[j].orderStatus = OrderStatus.EXECUTED
                buy_limit_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_limit_orders[j], (currentSharePrice + buy_limit_orders[j].limitPrice)/2)

                executed_orders_and_price.append(
                    (buy_limit_orders[j], (currentSharePrice + buy_limit_orders[j].limitPrice)/2))
                
                buy_limit_orders[j].quantityExecuted = buy_limit_orders[j].quantity
                
            else:
                total_cost = (buy_limit_orders[j].dynamicQuantity - (quantity_so_far - wants_to_sell)) * (currentSharePrice + buy_limit_orders[j].limitPrice)/2
                # Then partial execution, and status remains as pending
                buy_limit_orders[j].dynamicQuantity = (quantity_so_far - wants_to_sell)
                buy_limit_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=buy_limit_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=buy_limit_orders[j].dynamicQuantity, 
                    quantityExecuted=buy_limit_orders[j].quantity - buy_limit_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_limit_orders[j], (currentSharePrice + buy_limit_orders[j].limitPrice)/2)

                # MAYBE
                executed_orders_and_price.append(
                    (buy_limit_orders[j], (currentSharePrice + buy_limit_orders[j].limitPrice)/2))
                
                buy_limit_orders[j].quantityExecuted = buy_limit_orders[j].quantity - buy_limit_orders[j].dynamicQuantity
                
        
        Order.objects.filter(id=sell_market_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_market_orders[i].quantity)
        sell_market_orders[i].orderStatus = OrderStatus.EXECUTED
        sell_market_orders[i].dynamicQuantity = 0
        new_price = total_cost/wants_to_sell

        # Update in Shares_Owned
        updateSharesOwnedForSellOrder(sell_market_orders[i])

        executed_orders_and_price.append(
            (sell_market_orders[i], new_price))
        
        sell_market_orders[i].quantityExecuted = sell_market_orders[i].quantity
        
        print("executed_orders_and_price: ", executed_orders_and_price)
        buy_limit_orders = removeExecutedOrders(buy_limit_orders)

        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # MAYBE id=stock.id
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        currentSharePrice = new_price

        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

    sell_market_orders = removeExecutedOrders(sell_market_orders)
    
    # Send all these executed orders along with the price at which they were executed
    sendExecutedOrdersToTrades(executed_orders_and_price)
    return sell_market_orders, buy_market_orders, buy_limit_orders


def executeSellLimitOrders(stock, sell_limit_orders, buy_market_orders, buy_limit_orders):
    # TODO - DONE
    executed_orders_and_price = []
    # Matching sell limit orders with buy market orders
    for i, sell_order in enumerate(sell_limit_orders):
        if not isValidTransaction(sell_order):
            continue
        # First we match against other market buy orders
        wants_to_sell = sell_order.dynamicQuantity
        available_to_sell = 0
        index = -1
        currentSharePrice = stock.currentSharePrice
        for j, buy_order in enumerate(buy_market_orders):
            if buy_order.user == sell_order.user or currentSharePrice < sell_order.limitPrice or (not isValidTransaction(buy_order)):
                continue
            available_to_sell += buy_order.dynamicQuantity
            if available_to_sell >= wants_to_sell:
                index = j
                break
        print("++++++++++++================= ")
        print("Stock: ", sell_order.stock.stockName)
        print("User: ", sell_order.user.USERNAME_FIELD)
        print("Sell Limit - Buy Market")
        print("wants_to_sell", wants_to_sell)
        print("available_to_sell:", available_to_sell)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue
        
        Stock.objects.filter(stockId=sell_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        for j in range(index + 1):
            if buy_market_orders[j].user == sell_order.user or currentSharePrice < sell_order.limitPrice or (not isValidTransaction(buy_market_orders[j])):
                continue
            quantity_so_far += buy_market_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_sell:
                total_cost = buy_market_orders[j].dynamicQuantity * (currentSharePrice + sell_order.limitPrice)/2
                # Then full order get executed, and updates status
                Order.objects.filter(id=buy_market_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_market_orders[j].quantity)
                buy_market_orders[j].orderStatus = OrderStatus.EXECUTED
                buy_market_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_market_orders[j], (currentSharePrice + sell_order.limitPrice)/2)

                executed_orders_and_price.append(
                    (buy_market_orders[j], (currentSharePrice + sell_order.limitPrice)/2))
                
                buy_market_orders[j].quantityExecuted = buy_market_orders[j].quantity
            else:
                total_cost = (buy_market_orders[j].dynamicQuantity - (quantity_so_far - wants_to_sell)) * (currentSharePrice + sell_order.limitPrice)/2
                # Then partial execution, and status remains as pending
                buy_market_orders[j].dynamicQuantity = (quantity_so_far - wants_to_sell)
                buy_market_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=buy_market_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=quantity_so_far - wants_to_sell, 
                    quantityExecuted=buy_market_orders[j].quantity - buy_market_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_market_orders[j], (currentSharePrice + sell_order.limitPrice)/2)

                # MAYBE
                executed_orders_and_price.append(
                    (buy_market_orders[j], (currentSharePrice + sell_order.limitPrice)/2))
                
                buy_market_orders[j].quantityExecuted = buy_market_orders[j].quantity - buy_market_orders[j].dynamicQuantity
                

        Order.objects.filter(id=sell_limit_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_limit_orders[i].quantity)
        sell_limit_orders[i].orderStatus = OrderStatus.EXECUTED
        sell_limit_orders[i].dynamicQuantity = 0

        new_price = total_cost/wants_to_sell

        # Update in Shares_Owned
        updateSharesOwnedForSellOrder(sell_limit_orders[i])

        executed_orders_and_price.append(
            (sell_limit_orders[i], new_price))

        sell_limit_orders[i].quantityExecuted = sell_limit_orders[i].quantity
        
        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # MAYBE id=stock.id
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        #currentSharePrice = new_price
        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

        print("executed_orders_and_price: ", executed_orders_and_price)
        buy_market_orders = removeExecutedOrders(buy_market_orders)

    sell_limit_orders = removeExecutedOrders(sell_limit_orders)

    # Matching sell limit orders with buy limit orders
    for i, sell_order in enumerate(sell_limit_orders):
        if not isValidTransaction(sell_order):
            continue
        wants_to_sell = sell_order.dynamicQuantity
        available_to_sell = 0
        index = -1
        # First check if its possible, i.e. if there are enough buyers to accomodate for this seller
        for j, buy_order in enumerate(buy_limit_orders):
            if buy_order.user == sell_order.user or buy_order.limitPrice < sell_order.limitPrice or (not isValidTransaction(buy_order)):
                continue
            available_to_sell += buy_order.dynamicQuantity
            if available_to_sell >= wants_to_sell:
                index = j
                break
        
        print("++++++++++++================= ")
        print("Stock: ", sell_order.stock.stockName)
        print("User: ", sell_order.user.USERNAME_FIELD)
        print("Sell Limit - Buy Limit")
        print("wants_to_sell", wants_to_sell)
        print("available_to_sell:", available_to_sell)
        print("index:", index)
        # Now execute these orders till ith index, and if there are any partially completed orders
        # then let them remain in pending state. But for others we shall marks them as executed
        if index == -1:
            # Then trade not possible
            continue

        Stock.objects.filter(stockId=sell_order.stock.stockId).update(lastTradedAt=timezone.now())

        quantity_so_far = 0
        total_cost = 0
        for j in range(index + 1):
            if buy_limit_orders[j].user == sell_order.user or buy_limit_orders[j].limitPrice < sell_order.limitPrice or (not isValidTransaction(buy_limit_orders[j])):
                continue
            quantity_so_far += buy_limit_orders[j].dynamicQuantity
            if quantity_so_far <= wants_to_sell:
                total_cost = buy_limit_orders[j].dynamicQuantity * (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2
                # Then full order get executed, and updates status
                Order.objects.filter(id=buy_limit_orders[j].id).update(
                    orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=buy_limit_orders[j].quantity)
                buy_limit_orders[j].orderStatus = OrderStatus.EXECUTED
                buy_limit_orders[j].dynamicQuantity = 0

                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_limit_orders[j], (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2)

                executed_orders_and_price.append(
                    (buy_limit_orders[j], (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2))
                
                buy_limit_orders[j].quantityExecuted = buy_limit_orders[j].quantity
            else:
                total_cost = (buy_limit_orders[j].dynamicQuantity - (quantity_so_far - wants_to_sell)) * (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2
                # Then partial execution, and status remains as pending
                buy_limit_orders[j].dynamicQuantity = (quantity_so_far - wants_to_sell)
                buy_limit_orders[j].orderStatus = OrderStatus.PARTIAL
                Order.objects.filter(id=buy_limit_orders[j].id).update(
                    orderStatus=OrderStatus.PARTIAL, dynamicQuantity=quantity_so_far - wants_to_sell, 
                    quantityExecuted=buy_limit_orders[j].quantity - buy_limit_orders[j].dynamicQuantity)
                
                # Update in Shares_Owned
                updateSharesOwnedForBuyOrder(buy_limit_orders[j], (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2)

                # MAYBE
                executed_orders_and_price.append(
                    (buy_limit_orders[j], (sell_order.limitPrice + buy_limit_orders[j].limitPrice)/2))
                
                buy_limit_orders[j].quantityExecuted = buy_limit_orders[j].quantity - buy_limit_orders[j].dynamicQuantity
                
        
        Order.objects.filter(id=sell_limit_orders[i].id).update(
            orderStatus=OrderStatus.EXECUTED, dynamicQuantity=0, quantityExecuted=sell_limit_orders[i].quantity)
        sell_limit_orders[i].orderStatus = OrderStatus.EXECUTED
        sell_limit_orders[i].dynamicQuantity = 0
        
        new_price = total_cost/wants_to_sell

        # Update in Shares_Owned
        updateSharesOwnedForSellOrder(sell_limit_orders[i])

        executed_orders_and_price.append(
            (sell_limit_orders[i], new_price))
        
        sell_limit_orders[i].quantityExecuted = sell_limit_orders[i].quantity
        
        print("executed_orders_and_price: ", executed_orders_and_price)
        buy_limit_orders = removeExecutedOrders(buy_limit_orders)

        # Updating stock price
        Stock.objects.filter(stockId=stock.stockId).update(     # MAYBE id=stock.id
            currentSharePrice=new_price)
        stock.currentSharePrice = new_price
        #currentSharePrice = new_price
        new_stock_history = StockPriceHistory(stock=stock, stockPrice=new_price, updatedAt=timezone.now())
        new_stock_history.save()

    sell_limit_orders = removeExecutedOrders(sell_limit_orders)
    
    # Send all these executed orders along with the price at which they were executed
    sendExecutedOrdersToTrades(executed_orders_and_price)
    return sell_limit_orders, buy_market_orders, buy_limit_orders


def executeOrder(stockName, orderLists):
    #print("Executing orders for: ", stockName)
    stock = Stock.objects.get(stockName=stockName)
    #currentSharePrice = stock.currentSharePrice

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

    #print("Exiting execute orders.............................")
    return orderLists
    # TODO - DONE: Update the market price if limit order transactions occur inside of each function
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

        '''''
        print("######################################111111111")
        pprint(pendingOrders)
        print("######################################222222222")
        '''

        all_stocks = Stock.objects.all()
        print("Stock time updates: ")
        for stock in all_stocks:
            print(stock.stockName, " - ", stock.lastTradedAt)
