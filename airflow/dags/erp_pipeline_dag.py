"""
ERP data pipeline DAG.

Orchestrates the Silver and Gold batch transformations on a schedule,
with Gold explicitly depending on Silver's successful completion.
The Bronze streaming job is intentionally NOT scheduled here -- it's a
continuously-running process started independently, since Airflow's
task model is built for jobs that complete, not infinite streams.
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
    description="Silver and Gold layer transformations for ERP events",
    default_args=default_args,
    schedule=timedelta(hours=1),
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["erp", "silver", "gold"],
) as dag:

    run_silver_transform = BashOperator(
        task_id="silver_transform_erp",
        bash_command=(
            "cd /opt/stream-processor && "
            "python jobs/silver_transform_erp.py"
        ),
    )

    run_gold_aggregate = BashOperator(
        task_id="gold_aggregate_erp",
        bash_command=(
            "cd /opt/stream-processor && "
            "python jobs/gold_aggregate_erp.py"
        ),
    )

    # This single line is what makes it a DAG rather than two independent
    # tasks: Gold will only start after Silver finishes successfully.
    # If Silver fails, Gold is automatically skipped, not run on stale data.
    run_silver_transform >> run_gold_aggregate
