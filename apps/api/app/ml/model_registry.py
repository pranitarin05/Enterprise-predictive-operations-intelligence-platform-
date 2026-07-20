"""
MLflow model loading.

Loads the raw XGBoost Booster directly from the downloaded artifact
files, rather than using mlflow.xgboost.load_model()'s sklearn-wrapper
reconstruction -- which has a known compatibility bug between MLflow's
flavor-loading logic and newer xgboost versions (_estimator_type
undefined). Loading the Booster directly is more robust and is a
common, legitimate pattern for production model serving.
"""

import logging
import os

import mlflow.artifacts
import xgboost as xgb

logger = logging.getLogger("epoip.ml.model_registry")

MLFLOW_TRACKING_URI = "http://localhost:5000"
MODEL_NAME = "shipment_delay_predictor"
MODEL_STAGE_URI = f"models:/{MODEL_NAME}/latest"

SUPPLIER_RISK_SCORES = {
    "Global Parts Co": 0.485507,
    "FastTrack Logistics": 0.461111,
    "Acme Supplies": 0.226064,
    "Prime Vendor Group": 0.224806,
    "Reliable Freight Inc": 0.201044,
}
DEFAULT_RISK_SCORE = sum(SUPPLIER_RISK_SCORES.values()) / len(SUPPLIER_RISK_SCORES)

_model = None


def _find_model_file(local_dir: str) -> str:
    """
    MLflow's xgboost flavor saves the native model file alongside
    metadata (MLmodel, conda.yaml, requirements.txt, etc). We locate
    the actual model file by extension rather than assuming a fixed
    filename, since xgboost's default save format/name can vary by
    version (json/ubj/deprecated).
    """
    for filename in os.listdir(local_dir):
        if filename.split(".")[-1] in ("json", "ubj", "xgb", "bin", "model"):
            return os.path.join(local_dir, filename)
    raise FileNotFoundError(f"No xgboost model file found in {local_dir}: {os.listdir(local_dir)}")


def get_model() -> xgb.Booster:
    global _model
    if _model is None:
        import mlflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

        logger.info(f"Downloading model artifacts from {MODEL_STAGE_URI}...")
        local_dir = mlflow.artifacts.download_artifacts(artifact_uri=MODEL_STAGE_URI)
        model_file = _find_model_file(local_dir)

        logger.info(f"Loading Booster from {model_file}...")
        booster = xgb.Booster()
        booster.load_model(model_file)
        _model = booster
        logger.info("Model loaded successfully.")
    return _model


def get_supplier_risk_score(supplier: str) -> float:
    return SUPPLIER_RISK_SCORES.get(supplier, DEFAULT_RISK_SCORE)
