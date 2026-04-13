"""Constants and utilities for presentation layer."""

# Currency symbols for display
CURRENCY_SYMBOLS = {
    "ILS": "₪",
    "USD": "$",
    "EUR": "€",
}


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for display.

    Args:
        currency: Currency code (e.g., "ILS", "USD", "EUR")

    Returns:
        Currency symbol or the code itself if not found
    """
    return CURRENCY_SYMBOLS.get(currency, currency)
