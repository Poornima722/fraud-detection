from transaction_service import process_transaction


transaction = {
    "customer_id": "C001",
    "transaction_time": "2026-09-02T11:00:00+05:30",
    "merchant": "integration_test_store",
    "category": "grocery",
    "amount": 900.00,
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


result = process_transaction(transaction)

print("Full transaction processing successful!")

print("\nResult:")
print(result)