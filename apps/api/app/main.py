"""
FastAPI application entrypoint.
"""

import logging
import os

# Set MinIO/S3 credentials for MLflow's artifact downloads BEFORE any
# MLflow-related imports happen. MLflow's S3 artifact repo uses boto3
# under the hood, which reads these standard AWS_* env vars -- setting
# them here (rather than relying on the terminal's shell environment)
# ensures they're always present regardless of how/where the server
# is started (a real deployment would set these via K8s Secrets instead).
os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minioadmin")

from fastapi import FastAPI

from app.api.routes import health, auth, predictions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("epoip.api")

app = FastAPI(
    title="EPOIP API",
    description="Enterprise Predictive Operations Intelligence Platform — Backend API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predictions.router)


@app.on_event("startup")
def on_startup():
    logger.info("EPOIP API starting up...")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("EPOIP API shutting down...")
