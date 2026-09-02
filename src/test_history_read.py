from supabase_admin import supabase_admin

response = (
    supabase_admin
    .table("transactions")
    .select("*")
    .eq("customer_id", "C001")
    .order("transaction_time")
    .execute()
)

print("Customer history:")
for txn in response.data:
    print(
        txn["transaction_time"],
        "→ ₹",
        txn["amount"]
    )