from django.test import TestCase
from numpy import quantile

from models import *
from django.contrib.auth import get_user_model
from stocks.models import Stock


class OrderTypesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        OrderTypes.objects.create()

    def test_choices_method(self):
        orderTypes = OrderTypes.objects.get(id=1)
        # Checking for the Enum(s)
        expected_tuple = [(orderTypes.MARKET, "MARKET"),
                          (orderTypes.LIMIT, "LIMIT")]
        self.assertDictEqual(OrderTypes.choices(orderTypes), expected_tuple)


class OrderDirectionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        OrderDirections.objects.create()

    def test_choices_method(self):
        orderDirections = OrderDirections.objects.get(id=1)
        # Checking for the Enum(s)
        expected_tuple = [(OrderDirections.BUY, "BUY"),
                          (OrderDirections.SELL, "SELL")]
        # TODO: Check This function
        self.assertDictEqual(OrderDirections.choices(
            orderDirections), expected_tuple)


class OrderStatusTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        OrderStatus.objects.create()

    def test_choices_method(self):
        orderStatus = OrderStatus.objects.get(id=1)
        # Checking for the Enum(s)
        expected_tuple = [(OrderStatus.PENDING, "PENDING"),
                          (OrderStatus.EXECUTED, "EXECUTED"),
                          (OrderStatus.PARTIAL, "PARTIAL")]
        # TODO: Check This function
        self.assertDictEqual(OrderStatus.choices(
            orderStatus), expected_tuple)


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
