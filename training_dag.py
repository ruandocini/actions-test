from datetime import datetime, timedelta
from airflow import DAG
from generator.dag_wrapper import DagWrapper
from generator.new_relic_integration import NewRelicIntegration
from generator.alerts_integration import AlertsIntegration
from airflow.models import Variable
            
training_config = "models/dummy_model/dummy_model.json"
branch_name = "feature/training1"
nr_integration = NewRelicIntegration()
alert = AlertsIntegration("both")

DAG_NAME = "air-science-training"

default_args = {
    "owner": "data-science",
    "depends_on_past": False,
    "start_date": datetime.strptime("2024-04-09", "%Y-%m-%d"),
    "on_failure_callback": alert.task_fail_alert,
    "on_success_callback": nr_integration.task_success_new_relic_alert,
    "params": {
        "severity": 2,
    },
    "retry_delay": timedelta(seconds=60),
    "retries": 3,
}

dag = DAG(
    dag_id=DAG_NAME,
    default_args=default_args,
    catchup=False,
    schedule_interval="* * * * *",
    tags=[
        "science",
        "training"
    ],
)


env_vars = {
    "AWS_DEFAULT_REGION": "us-east-1",
    **Variable.get("var-air-science-starburst-credentials", deserialize_json=True)
}


execute_forecast = DagWrapper.create_base_pod_operator(
    dag=dag,
    task_name=f"execute-model-training",
    namespace="data-platform",
    version="base-v0.0.3",
    repository="science",
    branch=f'{branch_name}',
    workdir="models/",
    service_account_name="airflow",
    main_file="training/training.py",
    requirements="True",
    do_xcom_push=False,
    arguments=[
        "--training_config",
        f'{training_config}'
    ],
    env_vars=env_vars,
)

execute_forecast