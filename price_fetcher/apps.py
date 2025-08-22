from django.apps import AppConfig
import os
import threading


class PriceFetcherConfig(AppConfig):
    name = "price_fetcher"

    def ready(self) -> None:
        # Only start listeners in the main process (prevents double-start under runserver autoreload)
        if os.environ.get("RUN_MAIN") != "true":
            return

        from price_fetcher.connectors.all_streams import start_all
        threading.Thread(target=start_all, daemon=True).start()
