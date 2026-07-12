"""
Trains an XGBoost classifier to predict per-order shipment delay risk,
using each order's supplier (historically target-encoded) and order
value as features.

This is the correct framing for this problem: predicting delay risk
per individual order, using that order's own supplier's historical
risk rate -- computed strictly from training-period orders only, to
avoid label leakage. Earlier daily-aggregated versions diluted the
signal by blending multiple suppliers per day; this version doesn't.
"""

import pandas as pd
import mlflow
import mlflow.xgboost
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

MLFLOW_TRACKING_URI = "http://localhost:5000"
STORAGE_OPTIONS = {
    "key": "minioadmin",
    "secret": "minioadmin",
    "client_kwargs": {"endpoint_url": "http://localhost:9000"},
}


def load_data() -> pd.DataFrame:
    return pd.read_parquet(
        "s3://epoip-gold/feast_exports/order_level",
        storage_options=STORAGE_OPTIONS,
    )


def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("shipment_delay_prediction")

    data = load_data().sort_values("order_date").reset_index(drop=True)
    print(f"Loaded {len(data)} order-level rows.")
    print(f"Overall delay rate: {data['was_delayed'].mean():.2%}")

    split_idx = int(len(data) * 0.8)
    train_df = data.iloc[:split_idx].copy()
    test_df = data.iloc[split_idx:].copy()

    # Historical target encoding -- supplier risk computed from TRAINING
    # rows only, then applied to both train and test. This is the
    # leakage-safe way to turn "supplier name" into a numeric feature.
    supplier_risk = train_df.groupby("supplier")["was_delayed"].mean().rename("supplier_risk_score")
    print("\nSupplier risk scores (training period only):")
    print(supplier_risk.sort_values(ascending=False).to_string())

    overall_train_rate = train_df["was_delayed"].mean()
    train_df["supplier_risk_score"] = train_df["supplier"].map(supplier_risk)
    test_df["supplier_risk_score"] = test_df["supplier"].map(supplier_risk).fillna(overall_train_rate)

    feature_columns = ["supplier_risk_score", "amount_usd"]
    X_train, y_train = train_df[feature_columns], train_df["was_delayed"]
    X_test, y_test = test_df[feature_columns], test_df["was_delayed"]

    print(f"\nTrain rows: {len(X_train)} (positive rate {y_train.mean():.2%})")
    print(f"Test rows: {len(X_test)} (positive rate {y_test.mean():.2%})")

    params = {
        "n_estimators": 150,
        "max_depth": 4,
        "learning_rate": 0.1,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
    }

    with mlflow.start_run(run_name="xgboost_shipment_delay_v5_order_level"):
        mlflow.log_params(params)
        mlflow.log_param("train_rows", len(X_train))
        mlflow.log_param("test_rows", len(X_test))
        mlflow.log_param("features", feature_columns)
        mlflow.log_param("grain", "per_order")
        mlflow.log_param("supplier_encoding", "historical_target_encoding_train_only")

        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_pred_proba),
        }
        mlflow.log_metrics(metrics)

        mlflow.xgboost.log_model(
            model, artifact_path="model", registered_model_name="shipment_delay_predictor",
        )

        print("\nFeature importances:")
        for name, importance in zip(feature_columns, model.feature_importances_):
            print(f"  {name}: {importance:.4f}")

        print("\nTraining complete. Metrics:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")

        run_id = mlflow.active_run().info.run_id
        print(f"\nView at: {MLFLOW_TRACKING_URI}/#/experiments/1/runs/{run_id}")


if __name__ == "__main__":
    main()
