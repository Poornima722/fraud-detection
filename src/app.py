from flask import Flask, jsonify, request
from flask_cors import CORS

from transaction_service import process_transaction
from model_performance_service import calculate_model_performance
from analyst_decision_service import (
    create_otp_challenge,
    get_risk_level_for_transaction,
    save_analyst_decision,
    get_recent_analyst_decisions,
    resolve_otp_challenge,
    verify_otp_challenge,
)

ALLOWED_ACTIONS = {"APPROVE", "TRIGGER_OTP", "BLOCK"}

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "message": "API is running"})


@app.get("/api/model-performance")
def model_performance():
    try:
        return jsonify(calculate_model_performance())
    except Exception:
        return jsonify({"error": "Failed to calculate model performance."}), 500


@app.post("/api/transactions/analyze")
def analyze_transaction():
    transaction = request.get_json(silent=True)

    if not isinstance(transaction, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    customer_id = transaction.get("customer_id")
    if customer_id is None or customer_id == "":
        return jsonify({"error": "customer_id is required."}), 400

    try:
        result = process_transaction(transaction)
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        print("analysis error:", repr(exc))
        raise
    response = {}
    for key in (
        "transaction_id",
        "fraud_probability",
        "threshold",
        "decision",
        "risk_level",
        "decision_reason",
        "evidence",
    ):
        if key in result:
            response[key] = result[key]

    return jsonify(response)


@app.post("/api/transactions/<transaction_id>/decision")
def record_transaction_decision(transaction_id):
    if not transaction_id:
        return jsonify({"error": "transaction_id is required."}), 400

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    action = payload.get("action")
    if action is None or action == "":
        return jsonify({"error": "action is required."}), 400

    if action not in ALLOWED_ACTIONS:
        return jsonify({
            "error": "action must be one of APPROVE, TRIGGER_OTP, or BLOCK."
        }), 400

    try:
        risk_level = get_risk_level_for_transaction(transaction_id)
        response = save_analyst_decision(transaction_id, risk_level, action)
        saved = response.data[0] if response.data else {}
        status = "saved"
        if action == "TRIGGER_OTP":
            create_otp_challenge(transaction_id, risk_level)
            status = "awaiting_verification"
        elif action == "APPROVE":
            status = "approved"
        elif action == "BLOCK":
            status = "blocked"
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to save analyst decision."}), 500

    result = {
        "transaction_id": saved.get("transaction_id", transaction_id),
        "risk_level": saved.get("risk_level", risk_level),
        "action": saved.get("action", action),
        "status": status,
    }

    if saved.get("created_at") is not None:
        result["created_at"] = saved["created_at"]

    return jsonify(result)


@app.post("/api/transactions/<transaction_id>/verify-otp")
def verify_transaction_otp(transaction_id):
    if not transaction_id:
        return jsonify({"error": "transaction_id is required."}), 400

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    otp = payload.get("otp")
    if not isinstance(otp, str) or len(otp) != 6 or not otp.isdigit():
        return jsonify({"error": "otp must be a 6-digit code."}), 400

    try:
        challenge, is_valid = verify_otp_challenge(transaction_id, otp)
        action = "APPROVE" if is_valid else "BLOCK"
        save_analyst_decision(transaction_id, challenge["risk_level"], action)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to verify OTP."}), 500

    if is_valid:
        return jsonify({
            "transaction_id": transaction_id,
            "status": "approved",
            "action": "APPROVE",
            "message": "OTP VERIFIED - Transaction APPROVED",
        })

    return jsonify({
        "transaction_id": transaction_id,
        "status": "blocked",
        "action": "BLOCK",
        "message": "OTP FAILED - Transaction BLOCKED",
    })


def resolve_transaction_callback(transaction_id, passed):
    if not transaction_id:
        return jsonify({"error": "transaction_id is required."}), 400

    try:
        challenge = resolve_otp_challenge(transaction_id, passed)
        action = "APPROVE" if passed else "BLOCK"
        save_analyst_decision(transaction_id, challenge["risk_level"], action)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to resolve customer callback."}), 500

    return jsonify({
        "transaction_id": transaction_id,
        "status": "approved" if passed else "blocked",
        "action": action,
        "message": "OTP VERIFIED" if passed else "OTP FAILED / EXPIRED",
    })


@app.post("/api/transactions/<transaction_id>/otp-success")
def transaction_otp_success(transaction_id):
    return resolve_transaction_callback(transaction_id, True)


@app.post("/api/transactions/<transaction_id>/otp-failure")
def transaction_otp_failure(transaction_id):
    return resolve_transaction_callback(transaction_id, False)

@app.get("/api/audit")
def get_audit():
    try:
        decisions = get_recent_analyst_decisions(limit=5)
        return jsonify(decisions)
    except Exception:
        return jsonify({"error": "Failed to load audit trail."}), 500

    
if __name__ == "__main__":
    app.run(debug=True)

