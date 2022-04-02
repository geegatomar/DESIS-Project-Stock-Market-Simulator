from inspect import ClassFoundException
from django.test import TestCase
from stocks.models import *
from orders.models import *
from trades.models import *
from base.models import *


class StockModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Stock.objects.create(stockId="AMZN", stockName="AMAZON INC.",
                             fullCompanyName="AMAZON INCORPORATION PRIVATE LIMITED, USA",
                             currentSharePrice=2534.26,
                             sharesOutstanding=2000,
                             lastTradedAt='2006-10-25 14:30:59')

    def test_string_method(self):
        stocks = Stock.objects.get(stockId=1)
        expected_string = str(self.stockName)
        self.assertEqual(str(stocks), expected_string)


class StockPriceHistoryModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up Stock object for ForeignKey
        stocks = Stock.objects.create(stockId="MSFT", stockName="MICROSOFT INC.",
                                      fullCompanyName="MICROSOFT PRIVATE LIMITED, USA",
                                      currentSharePrice=235.26,
                                      sharesOutstanding=65000,
                                      lastTradedAt='2006-10-25 12:30:59')

        StockPriceHistory.objects.create(stock=stocks,
                                         stockPrice=232.85,
                                         updatedAt='2006-10-25 12:32:59')

    def test_string_method(self):
        stockPriceHistoryObject = StockPriceHistory.objects.get(id=1)
        expected_string = str(self.stock.stockName) + " - " + \
            str(self.stockPrice) + " - " + str(self.updatedAt)
        self.assertEqual(str(stockPriceHistoryObject), expected_string)
