import numpy as np
import pandas as pd


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two geographic coordinates in kilometers.
    """

    R = 6371

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

def calculate_basic_features(current_transaction, customer):
    """
    Calculate features based on the current transaction
    and customer information.
    """

    transaction_time = pd.to_datetime(
        current_transaction["transaction_time"]
    )

    dob = pd.to_datetime(
        customer["dob"]
    )

    # Same age calculation used during training
    customer_age = (
        transaction_time.year
        - dob.year
    )

    # Time-based features
    hour = transaction_time.hour
    day_of_week = transaction_time.dayofweek
    month = transaction_time.month

    # Customer → merchant distance
    distance = haversine_distance(
        current_transaction["lat"],
        current_transaction["long"],
        current_transaction["merch_lat"],
        current_transaction["merch_long"]
    )

    return {
        "amt": current_transaction["amount"],
        "category": current_transaction["category"],
        "hour": hour,
        "customer_age": customer_age,
        "city_pop": current_transaction["city_pop"],
        "city": current_transaction["city"],
        "gender": current_transaction["gender"],
        "month": month,
        "merch_long": current_transaction["merch_long"],
        "day_of_week": day_of_week,
        "zip": current_transaction["zip"],
        "merch_lat": current_transaction["merch_lat"],
        "lat": current_transaction["lat"],
        "long": current_transaction["long"],
        "state": current_transaction["state"],
        "customer_merchant_distance_km": distance,
        "merchant": current_transaction["merchant"],
        "job": current_transaction.get("job", "")
    }

def build_model_features(current_transaction, customer, history):
    """
    Build the complete feature set required by the CatBoost model.
    """

    # Calculate basic/current-transaction features
    basic_features = calculate_basic_features(
        current_transaction,
        customer
    )

    # Calculate history-based features
    historical_features = calculate_historical_features(
        current_transaction,
        history
    )

    # Combine both
    all_features = {
        **basic_features,
        **historical_features
    }

    return pd.DataFrame([all_features])

def calculate_historical_features(current_transaction, history):
    """
    Calculate transaction-history-based features for a new transaction.

    current_transaction: dictionary containing the new transaction
    history: DataFrame containing previous transactions for the customer
    """

    current_time = pd.to_datetime(
        current_transaction["transaction_time"]
    )

    current_amount = current_transaction["amount"]

    # No previous transactions
    if history.empty:
        return {
            "prev_txn_amt": np.nan,
            "time_since_prev_txn": np.nan,
            "prev_avg_amt": np.nan,
            "amount_vs_prev_avg": np.nan,
            "log_amount_change_ratio": np.nan,
            "txn_count_1h": 0,
            "txn_count_24h": 0
        }

    # Make sure history is sorted chronologically
    history = history.sort_values("transaction_time").copy()

    history["transaction_time"] = pd.to_datetime(
        history["transaction_time"]
    )

    # Previous transaction
    previous = history[
        history["transaction_time"] < current_time
    ]

    if previous.empty:
        return {
            "prev_txn_amt": np.nan,
            "time_since_prev_txn": np.nan,
            "prev_avg_amt": np.nan,
            "amount_vs_prev_avg": np.nan,
            "log_amount_change_ratio": np.nan,
            "txn_count_1h": 0,
            "txn_count_24h": 0
        }

    # Most recent previous transaction
    prev_txn = previous.iloc[-1]

    prev_txn_amt = prev_txn["amount"]

    time_since_prev_txn = (
        current_time - prev_txn["transaction_time"]
    ).total_seconds() / 60

    # Average amount of all previous transactions
    prev_avg_amt = previous["amount"].mean()

    amount_vs_prev_avg = (
        current_amount / prev_avg_amt
    )

    amount_change_ratio = (
        current_amount / prev_txn_amt
    )

    log_amount_change_ratio = np.log(
        amount_change_ratio
    )

    # Transactions within previous 1 hour
    one_hour_ago = current_time - pd.Timedelta(hours=1)

    txn_count_1h = len(
        previous[
            previous["transaction_time"] >= one_hour_ago
        ]
    )

    # Transactions within previous 24 hours
    twenty_four_hours_ago = (
        current_time - pd.Timedelta(hours=24)
    )

    txn_count_24h = len(
        previous[
            previous["transaction_time"] >= twenty_four_hours_ago
        ]
    )

    return {
        "prev_txn_amt": prev_txn_amt,
        "time_since_prev_txn": time_since_prev_txn,
        "prev_avg_amt": prev_avg_amt,
        "amount_vs_prev_avg": amount_vs_prev_avg,
        "log_amount_change_ratio": log_amount_change_ratio,
        "txn_count_1h": txn_count_1h,
        "txn_count_24h": txn_count_24h
    }