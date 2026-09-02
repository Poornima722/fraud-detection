from supabase_client import supabase


test_transactions = [
    {
        "customer_id": "C001",
        "transaction_time": "2026-09-01T20:00:00+05:30",
        "merchant": "test_store",
        "category": "grocery",
        "amount": 500.00,
        "gender": "F",
        "city": "Bengaluru",
        "state": "Karnataka",
        "zip": 560001,
        "lat": 12.9716,
        "long": 77.5946,
        "city_pop": 10000000,
        "merch_lat": 12.9616,
        "merch_long": 77.6046
    },
    {
        "customer_id": "C001",
        "transaction_time": "2026-09-01T20:30:00+05:30",
        "merchant": "test_store",
        "category": "grocery",
        "amount": 700.00,
        "gender": "F",
        "city": "Bengaluru",
        "state": "Karnataka",
        "zip": 560001,
        "lat": 12.9716,
        "long": 77.5946,
        "city_pop": 10000000,
        "merch_lat": 12.9616,
        "merch_long": 77.6046
    },
    {
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
]


response = (
    supabase
    .table("transactions")
    .insert(
        test_transactions,
        returning="minimal"
    )
    .execute()
)

print("Test history inserted successfully!")