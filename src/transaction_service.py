import pandas as pd

from supabase_admin import supabase_admin
from feature_engineering import build_model_features
from predict import predict_fraud


def get_customer(customer_id):
    """
    Fetch customer profile from Supabase.
    """

    response = (
        supabase_admin
        .table("customers")
        .select("*")
        .eq("customer_id", customer_id)
        .single()
        .execute()
    )

    return response.data


def get_customer_history(customer_id):
    """
    Fetch previous transactions for a customer.
    """

    response = (
        supabase_admin
        .table("transactions")
        .select("*")
        .eq("customer_id", customer_id)
        .order("transaction_time")
        .execute()
    )

    return pd.DataFrame(response.data)

def save_transaction(transaction):
    """
    Save a transaction and return the generated transaction ID.
    """

    response = (
        supabase_admin
        .table("transactions")
        .insert(transaction)
        .execute()
    )

    return response


def save_prediction(transaction_id, result, model_version="catboost-v1"):
    """
    Save the model prediction to the predictions table.
    """

    prediction = {
        "transaction_id": transaction_id,
        "fraud_probability": result["fraud_probability"],
        "threshold": result["threshold"],
        "decision": result["decision"],
        "model_version": model_version
    }

    response = (
        supabase_admin
        .table("predictions")
        .insert(
            prediction,
            returning="minimal"
        )
        .execute()
    )

    return response

def process_transaction(transaction):
    """
    Process a new transaction, generate a fraud prediction,
    and save both the transaction and prediction.
    """

    customer_id = transaction["customer_id"]

    # 1. Get customer profile
    customer = get_customer(customer_id)

    if customer is None:
        raise ValueError(
            f"Customer '{customer_id}' not found."
        )

    # 2. Get transaction history
    history = get_customer_history(customer_id)

    # 3. Build model features
    model_features = build_model_features(
        transaction,
        customer,
        history
    )

    # 4. Generate fraud prediction
    result = predict_fraud(
        model_features.iloc[0].to_dict()
    )

    # 5. Save transaction
    transaction_response = save_transaction(transaction)

    # 6. Get generated transaction ID
    transaction_id = transaction_response.data[0]["transaction_id"]

    # 7. Save prediction
    save_prediction(
        transaction_id,
        result
    )

    # 8. Return prediction + transaction ID
    return {
        "transaction_id": transaction_id,
        **result
    }