import secrets

from supabase_admin import supabase_admin
from evidence_engine import get_risk_level


OTP_CHALLENGES = {}


def get_risk_level_for_transaction(transaction_id):
    """
    Load the stored prediction for a transaction and map it
    to the existing risk-level policy.
    """

    response = (
        supabase_admin
        .table("predictions")
        .select("fraud_probability")
        .eq("transaction_id", transaction_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            f"No prediction found for transaction '{transaction_id}'."
        )

    return get_risk_level(response.data[0]["fraud_probability"])


def save_analyst_decision(transaction_id, risk_level, action):
    """
    Save an analyst decision to the analyst_decisions table.
    """

    decision = {
        "transaction_id": transaction_id,
        "risk_level": risk_level,
        "action": action
    }

    response = (
        supabase_admin
        .table("analyst_decisions")
        .insert(decision)
        .execute()
    )

    return response


def create_otp_challenge(transaction_id, risk_level):
    """Create an in-memory OTP challenge for the demo flow."""

    otp = f"{secrets.randbelow(1000000):06d}"
    OTP_CHALLENGES[transaction_id] = {
        "otp": otp,
        "risk_level": risk_level,
        "status": "awaiting_verification",
    }
    return otp


def verify_otp_challenge(transaction_id, otp):
    """Resolve an in-memory OTP challenge and return its outcome."""

    challenge = OTP_CHALLENGES.get(transaction_id)
    if challenge is None:
        raise ValueError(
            f"No active OTP challenge found for transaction '{transaction_id}'."
        )

    if challenge["status"] != "awaiting_verification":
        raise ValueError("This OTP challenge has already been resolved.")

    is_valid = secrets.compare_digest(challenge["otp"], otp)
    challenge["status"] = "verified" if is_valid else "failed"
    return challenge, is_valid


def resolve_otp_challenge(transaction_id, passed):
    """Resolve the in-memory challenge from a simulated customer callback."""

    challenge = OTP_CHALLENGES.get(transaction_id)
    if challenge is None:
        raise ValueError(
            f"No active OTP challenge found for transaction '{transaction_id}'."
        )

    if challenge["status"] != "awaiting_verification":
        raise ValueError("This OTP challenge has already been resolved.")

    challenge["status"] = "verified" if passed else "failed"
    return challenge

def get_recent_analyst_decisions(limit=5):
    response = (
        supabase_admin
        .table("analyst_decisions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []