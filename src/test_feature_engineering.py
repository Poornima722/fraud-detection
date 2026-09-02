from supabase_admin import supabase_admin
from feature_engineering import (calculate_historical_features, build_model_features)


# Current transaction we want to evaluate
current_transaction = {
    "customer_id": "C001",
    "transaction_time": "2026-09-01T21:00:00+05:30",
    "amount": 1200.00
}


# Fetch customer's transaction history
response = (
    supabase_admin
    .table("transactions")
    .select("*")
    .eq("customer_id", "C001")
    .order("transaction_time")
    .execute()
)

history = response.data

print("Transactions fetched:", len(history))

# Convert history into DataFrame
import pandas as pd

history_df = pd.DataFrame(history)

# Remove the current transaction from history
history_df = history_df[
    history_df["transaction_time"]
    != current_transaction["transaction_time"]
]

# Calculate historical features
features = calculate_historical_features(
    current_transaction,
    history_df
)

print("\nCalculated historical features:")

for name, value in features.items():
    print(f"{name}: {value}")

print("\n\nTesting first transaction:")

new_customer_transaction = {
    "customer_id": "NEW_CUSTOMER",
    "transaction_time": "2026-09-02T10:00:00+05:30",
    "amount": 800.00
}

empty_history = pd.DataFrame()

first_txn_features = calculate_historical_features(
    new_customer_transaction,
    empty_history
)

for name, value in first_txn_features.items():
    print(f"{name}: {value}")

print("\n\nTesting complete model features:")

customer = {
    "customer_id": "C001",
    "dob": "1998-05-15"
}

current_transaction = {
    "customer_id": "C001",
    "transaction_time": "2026-09-01T21:00:00+05:30",
    "merchant": "test_store",
    "category": "grocery",
    "amount": 1200.00,
    "gender": "F",
    "city": "Bengaluru",
    "state": "Karnataka",
    "zip": 560001,
    "lat": 12.9716,
    "long": 77.5946,
    "city_pop": 10000000,
    "merch_lat": 12.9616,
    "merch_long": 77.6046
}

model_features = build_model_features(
    current_transaction,
    customer,
    history_df
)

print("\nFeature columns:")
print(model_features.columns.tolist())

print("\nFeature values:")
print(model_features.T)