from django.apps import AppConfig
import threading


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    # This is where we begin our order matcher/executor as a dameon thread.
    def ready(self):
        from orders.executions import execute
        t = threading.Thread(target=execute.mainExecutor, daemon=True)
        t.start()
