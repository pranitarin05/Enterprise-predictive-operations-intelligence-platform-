FROM apache/airflow:2.10.3-python3.11

USER root

# Java is required for PySpark's JVM
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

# Same PySpark/Delta versions as our stream-processor service, kept in sync deliberately
RUN pip install --no-cache-dir \
    pyspark==3.5.3 \
    delta-spark==3.2.0 \
    pydantic-settings==2.6.0
