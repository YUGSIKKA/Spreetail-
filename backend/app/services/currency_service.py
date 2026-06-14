from decimal import Decimal

USD_TO_INR_RATE = Decimal("84.0")

def convert_to_inr(amount: Decimal, currency: str) -> tuple[Decimal, Decimal | None]:
    """
    Returns (amount_inr, usd_rate_used).
    """
    if currency.upper() == "USD":
        return amount * USD_TO_INR_RATE, USD_TO_INR_RATE
    return amount, None
