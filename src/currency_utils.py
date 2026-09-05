INR_TO_USD_RATE = 83.5


def convert_inr_to_usd(amount_inr):
    """
    Convert an INR transaction amount to USD
    for the ML model, which was trained on USD amounts.
    """
    return round(float(amount_inr) / INR_TO_USD_RATE, 3)