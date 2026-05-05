#from django.apps import AppConfig


#class SearchConfig(AppConfig):
#    default_auto_field = 'django.db.models.BigAutoField'
#   name = 'search'

from django.apps import AppConfig
import threading

class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'

    def ready(self):
        def _warmup():
            try:
                from .services.nlu_engine import ModernNLUEngine
                engine = ModernNLUEngine()
                engine.parse("buy sugar")
                engine.parse("sell wheat to UAE")
                print("[ZaraiLink] NLU warmup complete — system ready.")
            except Exception as e:
                print(f"[ZaraiLink] Warmup skipped: {e}")

        threading.Thread(target=_warmup, daemon=True).start()