from django.urls import path
from price_fetcher.views import get_prices

urlpatterns = [
    path("prices/", get_prices, name="get_prices"),
]
