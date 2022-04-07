from django.db import models

class Stock(models.Model):
    stockId = models.CharField(max_length=16, primary_key=True)
    stockName = models.CharField(max_length=128, unique=True)
    fullCompanyName = models.CharField(max_length=128)
    currentSharePrice = models.DecimalField(max_digits=16, decimal_places=3)
    sharesOutstanding = models.IntegerField()
    lastTradedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.stockName)

class StockPriceHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    stockPrice = models.DecimalField(max_digits=16, decimal_places=3)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.stock.stockName) + " - " + str(self.stockPrice) + " - " + str(self.updatedAt)
