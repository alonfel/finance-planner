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


def format_retirement_year(retirement_year, fallback: str = "Never") -> str:
    """Format retirement year for display.

    Consolidates the pattern of showing "Year X" or a fallback if None.

    Args:
        retirement_year: The retirement year (int) or None
        fallback: String to display if retirement_year is None

    Returns:
        Formatted string like "Year 17" or fallback value
    """
    if retirement_year:
        return f"Year {retirement_year}"
    return fallback
