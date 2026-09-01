# Fraud Detection

Machine learning based fraud detection system using CatBoost.

## Dataset

The project uses the Credit Card Fraud Detection dataset containing
transaction records from 2019–2020.

The raw CSV datasets are not included in this repository because of
their large size.

To reproduce the preprocessing pipeline:

1. Obtain the original dataset.
2. Place the CSV files in the project directory.
3. Run `data_cleaning.ipynb`.
4. This generates the processed Parquet files.
5. Run `catBoost.ipynb` to train/evaluate the model.

## Machine Learning

The project uses CatBoost with class weighting to handle the highly
imbalanced fraud/non-fraud classes.

Feature engineering includes:

- Transaction time features
- Customer age
- Time since previous transaction
- Previous transaction amount
- Log amount change ratio
- Previous average transaction amount
- Amount relative to previous average
- Transaction velocity
- Customer–merchant distance

## Model

Model: CatBoostClassifier

The final decision threshold was selected using validation data with
a cost-sensitive approach where a missed fraud was assigned 5× the
cost of a false positive.

Selected threshold: 0.78

## Final Test Performance

- PR-AUC: 0.9238
- Fraud Precision: 56.98%
- Fraud Recall: 93.05%
- Fraud F1-score: 0.7068