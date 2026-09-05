# AI Risk Manager — Fraud Detection & Investigation

An end-to-end machine learning based fraud detection and transaction risk investigation system built using CatBoost.

The system combines machine learning predictions with deterministic behavioral evidence, risk-based transaction routing, analyst investigation, simulated step-up verification, and an auditable decision trail.

### Workflow

**DETECT → EXPLAIN → INVESTIGATE → DECIDE**

---

## Features

- Real-time transaction risk analysis through a web dashboard
- CatBoost-based fraud probability prediction
- Cost-sensitive risk thresholding
- Three-tier risk classification:
  - LOW → Auto-Allow
  - MEDIUM → Analyst Review
  - HIGH → Auto-Block
- Historical behavioral feature engineering
- Transaction velocity analysis
- Transaction amount anomaly detection
- Customer–merchant geographic distance using Haversine distance
- Deterministic behavioral evidence generation
- Human-readable model decision reasoning
- Customer transaction history for investigation
- Analyst decision workflow
- Simulated step-up authentication flow
- Persistent analyst decision audit trail
- Global model performance evaluation
- INR transaction input with internal USD conversion for the trained model

---

## System Architecture

```text
                         WEB DASHBOARD
                              │
                              │ HTTP / JSON
                              ▼
                        FLASK BACKEND
                              │
                              ▼
                     TRANSACTION SERVICE
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
             ▼                ▼                 ▼
      Customer Lookup   Feature Engineering   History
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                       CATBOOST MODEL
                              │
                              ▼
                       FRAUD PROBABILITY
                              │
                              ▼
                         RISK POLICY
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  LOW      MEDIUM      HIGH
                   │          │          │
               AUTO-ALLOW   REVIEW   AUTO-BLOCK
                              │
                              ▼
                     ANALYST INVESTIGATION
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                 APPROVE   STEP-UP     BLOCK
                              │
                              ▼
                       AUDIT TRAIL
                              │
                              ▼
                     SUPABASE / POSTGRESQL
```

## Dataset

The project uses the Credit Card Fraud Detection dataset containing transaction records from 2019–2020.

The raw CSV datasets are not included in the repository because of their large size.

The preprocessing and model-training workflow is provided through:

- `data_cleaning.ipynb` — data cleaning and preprocessing
- `catBoost.ipynb` — model training, evaluation, and threshold analysis

The processed training and test datasets are generated as Parquet files during the pipeline.

---

## Machine Learning

The fraud detection model uses a `CatBoostClassifier` with class weighting to handle the highly imbalanced fraud/non-fraud classes.

Feature engineering captures transaction, temporal, behavioral, and spatial patterns, including:

- Transaction time and calendar features
- Customer age
- Previous transaction amount
- Time since previous transaction
- Amount change relative to customer history
- Transaction velocity over 1-hour and 24-hour windows
- Customer–merchant geographic distance using the Haversine formula

The trained model is stored in the `model/` directory.

---

## Risk Policy

The system uses a three-tier risk policy based on the fraud probability produced by the model.

| Fraud Probability | Risk Level | Operational Action |
|---|---|---|
| `< 0.25` | LOW | AUTO-ALLOW |
| `0.25 – < 0.78` | MEDIUM | ANALYST REVIEW |
| `≥ 0.78` | HIGH | AUTO-BLOCK |

The high-risk threshold of **0.78** was selected using validation data with a cost-sensitive approach.

A relative **1:5 fraud-cost assumption** was used during threshold selection, assigning a higher cost to missed fraud than to false positives.

The cost ratio is a relative evaluation assumption and does not represent a monetary loss value.

---

## Explainability & Behavioral Evidence

The system separates the explanation of the model's decision from the behavioral evidence detected in the transaction.

### Decision Reason

A deterministic explanation describes why the transaction was assigned its LOW, MEDIUM, or HIGH risk level and corresponding operational action.

### Behavioral Evidence

A separate deterministic evidence engine checks transaction features for observable risk signals such as:

- Unusually high transaction amounts compared with customer history
- Rapid successive transactions
- High transaction velocity
- Unusually large customer–merchant geographic distance

Evidence is generated independently of the model's fraud probability and risk level.

This allows a transaction to display genuine behavioral signals even when the overall model risk is LOW.

---

## Analyst Investigation

MEDIUM-risk transactions are routed to an analyst review workflow.

The analyst can:

- Approve the transaction
- Trigger a step-up verification challenge
- Block the transaction

The step-up verification flow is a simulated authentication lifecycle inspired by 3-D Secure (3DS).

It is a prototype simulation and does not represent a live payment-gateway or 3DS integration.

Analyst decisions are persisted in the audit trail for accountability.

---

## Model Performance

The saved CatBoost model is evaluated on the held-out test dataset using the same **0.78 classification threshold** used by the risk policy.

### Final Test Performance

- Evaluation samples: **555,719**
- PR-AUC: **0.9238**
- Fraud Precision: **56.98%**
- Fraud Recall: **93.05%**
- Fraud F1 Score: **70.68%**
- False Positive Rate: **0.27%**

### Confusion Matrix

```text
                 Actual
              Legit     Fraud
Pred Legit   552,067     149
Pred Fraud     1,507    1,996
```

## Application

The system provides an end-to-end transaction risk management workflow through a React web dashboard and Flask backend.

Key capabilities include:

- Live transaction fraud analysis
- Fraud probability and three-tier risk classification
- Automated allow/review/block actions
- Human-readable decision reasoning
- Deterministic behavioral evidence
- Customer transaction history for investigation
- Analyst review and decision workflow
- Simulated step-up verification
- Model performance evaluation
- Persistent audit trail of analyst decisions

---

## Technology Stack

**Machine Learning:** CatBoost, Pandas, NumPy, scikit-learn

**Backend:** Python, Flask, Flask-CORS

**Frontend:** React, Vite, JavaScript, CSS

**Database:** Supabase / PostgreSQL

**Model Storage:** CatBoost `.cbm` model

---

## Configuration & Running

Sensitive Supabase credentials are stored using environment variables and are not committed to the repository.

Create a `.env` file using `.env.example` as a template:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```
---

## Future Scope & Production Roadmap

- **Distributed Feature Store (Redis / Feast):** Replace on-the-fly feature calculation with a low-latency feature store to cache rolling customer behavioral features for high-throughput transaction scoring.

- **Production 3-D Secure (3DS) Webhook Pipeline:** Upgrade the simulated step-up challenge to integrate real EMVCo/3DS authentication flows and payment-gateway callbacks.

- **Dynamic Cost-Matrix Calibration:** Introduce automated model monitoring and retraining to recalibrate risk thresholds as transaction patterns and fraud-cost distributions evolve over time.

- **Real-Time Geolocation Feeds:** Integrate IP, device, and merchant-location telemetry to complement the static geographic features currently used by the prototype.
