from django.urls import path, include

urlpatterns = [
    path("api/", include("price_fetcher.urls")),
]
