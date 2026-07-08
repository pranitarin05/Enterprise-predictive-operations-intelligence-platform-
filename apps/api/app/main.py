"""
FastAPI application entrypoint.
"""

import logging

from fastapi import FastAPI

from app.api.routes import health, auth

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


@app.on_event("startup")
def on_startup():
    logger.info("EPOIP API starting up...")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("EPOIP API shutting down...")
