from django.contrib import admin

# Register your models here.
from .models import Trade
from .models import Shares_Owned

admin.site.register(Trade)
admin.site.register(Shares_Owned)
