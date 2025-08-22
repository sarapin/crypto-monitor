from rest_framework.decorators import api_view
from rest_framework.response import Response
from price_fetcher.serializer import PriceQueryParamsSerializer
from price_fetcher.services import fetch_prices


@api_view(["GET"])
def get_prices(request):
    serializer = PriceQueryParamsSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    data = fetch_prices(
        exchange=serializer.validated_data.get("exchange"),
        pair=serializer.validated_data.get("pair")
    )
    return Response(data)
