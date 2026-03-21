from django.apps import AppConfig


class TradeDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trade_data'

    def ready(self):
        from trade_data.signals import wire_transaction_signal
        wire_transaction_signal()
