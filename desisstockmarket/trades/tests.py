from unittest import expectedFailure
from django.test import TestCase
from numpy import quantile

from models import *
from django.contrib.auth import get_user_model
from orders.models import *
from stocks.models import Stock
from django.conf import settings


class OrderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting Up user for ForeignKey
        user = get_user_model()
        # Setting up Stock object for ForeignKey
        stocks = Stock.objects.create(stockId="MSFT", stockName="MICROSOFT INC.",
                                      fullCompanyName="MICROSOFT PRIVATE LIMITED, USA",
                                      currentSharePrice=235.26,
                                      sharesOutstanding=65000,
                                      lastTradedAt='2006-10-25 12:30:59')

        Order.objects.create(orderType=OrderTypes.LIMIT,
                             orderDirection=OrderDirections.SELL,
                             orderStatus=OrderStatus.PARTIAL,
                             stock=stocks,
                             quantity=2,
                             dynamicQuantity=1,
                             quantityExecuted=1,
                             limitPrice=236.25,
                             createdAt='2006-10-27 09:06:59',
                             updatedAt='2006-10-27 09:10:25',
                             user=user)

    def test_string_method(self):
        order = Order.objects.get(id=1)
        expected_string = str(self.stockName)
        price = str(" at Limit " + str(self.limitPrice) if self.orderType ==
                    'LIMIT' else "")
        orderStatus = ('EXECUTED' if self.orderStatus in (
            'OrderStatus.EXECUTED', 'EXECUTED', OrderStatus.EXECUTED)
            else 'PENDING' if self.orderStatus in (
            'OrderStatus.PENDING', 'PENDING', OrderStatus.PENDING)
            else 'PARTIAL')
        expected_string = str(self.orderType) + " order to " + str(self.orderDirection) + " " + str(
            self.quantity) + " " + str(self.stock) + " stock" + price + ": " + orderStatus
        self.assertEqual(str(order), expected_string)


class TradeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting Up user for ForeignKey
        user = get_user_model()
        # Setting up Stock object for ForeignKey
        stocks = Stock.objects.create(stockId="MSFT", stockName="MICROSOFT INC.",
                                      fullCompanyName="MICROSOFT PRIVATE LIMITED, USA",
                                      currentSharePrice=235.26,
                                      sharesOutstanding=65000,
                                      lastTradedAt='2006-10-25 12:30:59')
        # Setting up Order object for ForeginKey
        orders = Order.objects.create(orderType=OrderTypes.LIMIT,
                                      orderDirection=OrderDirections.SELL,
                                      orderStatus=OrderStatus.PARTIAL,
                                      stock=stocks,
                                      quantity=2,
                                      dynamicQuantity=1,
                                      quantityExecuted=1,
                                      limitPrice=236.25,
                                      createdAt='2006-10-27 09:06:59',
                                      updatedAt='2006-10-27 09:10:25',
                                      user=user)
        Trade.objects.create(order=orders,
                             executionPrice=238.87,
                             createdAt='2008-10-30 10:58:59',
                             updatedAt='2008-10-30 10:59:25',
                             user=user,
                             profit=2052.52)

        def test_str_method(self):
            trades = Trade.objects.get(id=1)
            expected_string = "Order " + \
                str(self.order) + " executed at price: " + \
                str(self.executionPrice)

            self.assertEqual(str(trades), expected_string)


class SharesOwnedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting Up user for ForeignKey
        user = get_user_model()
        # Setting up Stock object for ForeignKey
        stocks = Stock.objects.create(stockId="MSFT", stockName="MICROSOFT INC.",
                                      fullCompanyName="MICROSOFT PRIVATE LIMITED, USA",
                                      currentSharePrice=235.26,
                                      sharesOutstanding=65000,
                                      lastTradedAt='2006-10-25 12:30:59')

        Shares_Owned.objects.create(user=user,
                                    stock=stocks,
                                    quantity=24,
                                    avg_cost_price=356.56)

    def test_str_method(self):
        sharesOwned = Shares_Owned.objects.get(id=1)
        expected_string = "User " + \
            str(self.user.username) + " Stock: " + str(self.stock.stockName)
        self.assertEqual(str(sharesOwned), expected_string)
