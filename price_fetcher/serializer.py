# price_fetcher/serializers.py

from rest_framework import serializers

from crypto_monitor import settings


class PriceQueryParamsSerializer(serializers.Serializer):
    exchange = serializers.CharField(
        required=False,
        help_text="Optional. e.g. 'binance'. Leave blank for all exchanges."
    )
    pair = serializers.CharField(
        required=False,
        help_text="Optional. e.g. 'BTC_USDT'. Leave blank for all pairs."
    )

    def validate_exchange(self, value: str) -> str:
        val = value.lower()
        if val not in settings.EXCHANGES:
            raise serializers.ValidationError(f"Unknown exchange '{value}'.")
        return val

    def validate_pair(self, value: str) -> str:
        val = value.upper()
        if not all(ch.isalnum() or ch == "_" for ch in val):
            raise serializers.ValidationError(
                "Pair must contain only letters, digits, and underscore."
            )
        return val
