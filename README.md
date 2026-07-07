# EPOIP — Enterprise Predictive Operations Intelligence Platform

A multi-tenant predictive operations platform: streaming data ingestion,
ML forecasting/anomaly detection with explainability, and AI-generated
executive reports via a local-first, zero-cost stack (MinIO, Ollama,
self-hosted Kafka/Spark/Postgres/Redis/Qdrant).

## Status
🚧 In active development — Phase 1 (environment setup) complete.

## Stack
- Frontend: Next.js + TypeScript
- Backend: FastAPI
- Data: Kafka, Spark, Delta Lake (on MinIO), PostgreSQL, Redis
- ML: Scikit-learn, XGBoost, SHAP, LIME, MLflow, Feast
- AI: LangChain, LangGraph, Qdrant, Ollama
- Infra: Docker, Kubernetes, GitHub Actions

## Getting Started
See `docs/architecture/EPOIP-Architecture-Document.md` for full design.
Setup instructions land in Phase 2 (Docker Compose stack).
