from stocks.models import Stock, StockPriceHistory
from orders.models import Order, OrderDirections, OrderStatus, OrderTypes
from trades.models import Shares_Owned
from base.models import User
from pprint import pprint
from trades.transaction import trade
import time
import threading
from django.utils import timezone
from django.db.models import Q
import random
import decimal

def isValidTransaction(order):
    #''''
    if order.orderDirection == 'SELL':
        if Shares_Owned.objects.filter(user=order.user, stock=order.stock).exists():
            currently_owned = Shares_Owned.objects.filter(user=order.user, stock=order.stock)[0].quantity
            if(currently_owned < order.quantity):
                return False, "Insufficient shares to sell! You cannot sell stocks that you don\'t own."
        else:
            return False, "Insufficient shares to sell! You cannot sell stocks that you don\'t own."
    #'''

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
    
    return True, ""

def placeBotOrders():
    all_stocks = Stock.objects.all()
    all_bot_ids = [1, 2, 3]
    all_order_directions = ['BUY', 'SELL']
    all_order_types = ['MARKET', 'LIMIT']

    # for bot in all_bot_ids:
        # for i in range(3):
            # bot_user = User.objects.filter(id=bot)[0]
    bot = random.choice(all_bot_ids)
    bot_user = User.objects.get(id=bot)
    rm_stock = random.choice(all_stocks)
    rm_direction = random.choice(all_order_directions)
    rm_type = random.choice(all_order_types)
    rm_quantity = random.choice([1, 2, 3, 4])
    current_price = rm_stock.currentSharePrice
    delta = 5.1
    rm_lm_price = round(random.uniform(float(current_price)-delta, float(current_price)+delta), 3)
    #print("-----", rm_lm_price, "-----")
    #rm_lm_price = decimal.Decimal(rm_lm_price)
    
    # print(bot_user)
    # print(bot_user.id)
    # print(bot_user.username)
    # print(bot_user.account_value)
    # print(rm_stock)
    # print(rm_direction)
    # print(rm_type)
    # print(rm_quantity)
    # print(current_price)
    # print(rm_lm_price)
    
    new_order = Order(orderType=rm_type,
                    orderDirection=rm_direction,
                    orderStatus=OrderStatus.PENDING,
                    stock=rm_stock,
                    quantity=rm_quantity,
                    dynamicQuantity=rm_quantity,
                    quantityExecuted=0,
                    limitPrice=rm_lm_price,
                    createdAt=timezone.now(),
                    updatedAt=timezone.now(),
                    user=bot_user)
    if isValidTransaction(new_order):
        # print("Valid bot order")
        # print(new_order)
        new_order.save()
    