import pandas as pd

from supabase_admin import supabase_admin
from feature_engineering import build_model_features
from predict import predict_fraud
from evidence_engine import (
    generate_decision_reason,
    generate_evidence,
    get_risk_level,
)

def get_customer(customer_id):
    """
    Fetch customer profile from Supabase.
    """

    response = (
        supabase_admin
        .table("customers")
        .select("*")
        .eq("customer_id", customer_id)
        .execute()
    )

    customers = response.data or []
    return customers[0] if customers else None


def create_customer(customer_id, dob):
    """
    Create and return a customer profile for a new customer.
    """

    response = (
        supabase_admin
        .table("customers")
        .insert({"customer_id": customer_id, "dob": dob})
        .execute()
    )

    return response.data[0]


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
        dob = transaction.get("dob")
        if dob is None or dob == "":
            raise ValueError(
                f"dob is required for new customer '{customer_id}'."
            )
        customer = create_customer(customer_id, dob)

    # 2. Get transaction history
    history = get_customer_history(customer_id)

    # 3. Build model features
    model_features = build_model_features(
        transaction,
        customer,
        history
    )

    # 4. Generate fraud prediction
    features = model_features.iloc[0].to_dict()
    result = predict_fraud(features)

    result["risk_level"] = get_risk_level(result["fraud_probability"])
    result["decision_reason"] = generate_decision_reason(
        result["risk_level"],
        result["fraud_probability"],
        result["threshold"],
    )
    result["evidence"] = generate_evidence(features)

   # 5. Save transaction using the USD amount expected by the model
    transaction_to_save = {
        key: value for key, value in transaction.items()
        if key != "dob"
    }

    transaction_to_save["amount"] = model_features.iloc[0]["amt"]

    transaction_response = save_transaction(transaction_to_save)

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