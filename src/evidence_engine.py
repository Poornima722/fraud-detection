import math


def get_risk_level(fraud_probability):
    """
    Map a fraud probability to a discrete risk level.
    """

    if fraud_probability < 0.25:
        return "LOW"

    if fraud_probability < 0.78:
        return "MEDIUM"

    return "HIGH"


def _is_valid_number(value):
    """
    Return True when value is a finite numeric feature.
    """

    if value is None:
        return False

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False

    return math.isfinite(number)


def generate_evidence(features):
    """
    Inspect engineered transaction features and return
    deterministic, human-readable behavioral risk signals.
    """

    evidence = []

    # Amount anomaly
    amount_vs_prev_avg = features.get("amount_vs_prev_avg")

    if _is_valid_number(amount_vs_prev_avg):
        ratio = float(amount_vs_prev_avg)

        if ratio >= 2:
            evidence.append(
                f"Transaction amount is {ratio:.1f} times the customer's historical average"
            )

    # Rapid successive transaction
    time_since_prev_txn = features.get("time_since_prev_txn")

    if (
        _is_valid_number(time_since_prev_txn)
        and float(time_since_prev_txn) < 10
    ):
        minutes = float(time_since_prev_txn)

        evidence.append(
            f"Transaction occurred only {minutes:.1f} minutes after the previous transaction"
        )

    # Short-term velocity
    txn_count_1h = features.get("txn_count_1h")

    if _is_valid_number(txn_count_1h) and float(txn_count_1h) >= 3:
        count_1h = int(txn_count_1h)

        evidence.append(
            f"High transaction velocity: {count_1h} transactions in the last hour"
        )

    # 24-hour velocity
    txn_count_24h = features.get("txn_count_24h")

    if _is_valid_number(txn_count_24h) and float(txn_count_24h) >= 5:
        count_24h = int(txn_count_24h)

        evidence.append(
            f"High transaction velocity: {count_24h} transactions in the last 24 hours"
        )

    # Geographic distance
    customer_merchant_distance_km = features.get(
        "customer_merchant_distance_km"
    )

    if (
        _is_valid_number(customer_merchant_distance_km)
        and float(customer_merchant_distance_km) >= 500
    ):
        distance = float(customer_merchant_distance_km)

        evidence.append(
            f"Transaction location is unusually far from the customer ({distance:.0f} km)"
        )

    # No rule-triggered signals
    if not evidence:
        return ["No significant behavioral risk signals detected."]

    return evidence


def generate_decision_reason(risk_level, fraud_probability, threshold):
    """Explain the model outcome using the existing risk policy."""

    if risk_level == "LOW":
        return (
            "The model assesses this transaction as low risk, "
            "so it is automatically allowed."
        )

    if risk_level == "MEDIUM":
        return (
            "The model identifies elevated risk within the review range, "
            "so analyst verification is required."
        )

    return (
        "The model's fraud probability exceeds the high-risk threshold, "
        "triggering automatic blocking."
    )
