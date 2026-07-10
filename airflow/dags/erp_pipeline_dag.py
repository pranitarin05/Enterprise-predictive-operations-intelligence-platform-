"""
ERP data pipeline DAG.

Orchestrates the Silver-layer batch transformation on a schedule.
The Bronze streaming job is intentionally NOT scheduled here -- it's a
continuously-running process started independently (see Phase 9), since
Airflow's task model is built for jobs that complete, not infinite streams.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "epoip",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="erp_pipeline",
    description="Silver-layer transformation for ERP events",
    default_args=default_args,
    schedule=timedelta(hours=1),
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["erp", "silver", "bronze"],
) as dag:

    run_silver_transform = BashOperator(
        task_id="silver_transform_erp",
        bash_command=(
            "cd /opt/stream-processor && "
            "python jobs/silver_transform_erp.py"
        ),
    )
