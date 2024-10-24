import airflow
import pendulum
import docker
import time
from airflow import DAG
from datetime import timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator

#permission errors use:
#sudo chown ec2-user:ec2-user /home/ec2-user/airflow/dags/webscrape_dag.py
default_args = {
    'owner': 'airflow',
    'start_date': pendulum.today('UTC').subtract(days=1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def check_container(container_name = 'janusgraph-server', timeout = 200):
    client = docker.from_env()
    container = client.containers.get(container_name)
    elapsed_time = 0
    check_interval = 10

    while elapsed_time < timeout:
        container.reload()
        if container.attrs['State']['Health']['Status'] == 'healthy':
            return True
        sleep(check_interval)
        elapsed_time += check_interval
    
    raise TimeoutError(f"Container {container_name} did not become healthy within {timeout} seconds")

#Airflow will be started by aws lambda
scrapy_dag = DAG(
    'Webscraping',
    default_args=default_args,
    description='AWS lambda will trigger the DAG, pre_scrape >> scrapy >> post_scrape >> janugraph >> streamlit (optional)',
    schedule_interval=None,
)

#start Janusgraph
janusgraph_container = BashOperator(
    task_id='Start_Janusgraph',
    bash_command = 'echo "Starting Janusgraph container" && docker start janusgraph-server',
    dag = scrapy_dag
)

add_known_host = BashOperator(
    task_id='add_known_host',
    bash_command='ssh-keyscan -H 3.22.55.181 >> /opt/airflow/dags/id_rsa_airflow',
    dag= scrapy_dag,
)

#Pre-scrape python to clear tables:
prescrape_script = BashOperator(
    task_id='Pre-Scrape_script',
    bash_command = (
        'echo "Running pre-scrape script" && '
        'ssh -i /opt/airflow/dags/id_rsa_airflow ec2-user@3.22.55.181 "python3 /home/ec2-user/pre_scrape.py"'
    ),
    dag = scrapy_dag,
)

#Start the Webscrape and upload to staging database
scrapy_container = DockerOperator(
    task_id='Webscrape_Website',
    image='scrapy_project',  # Name of your Docker image
    api_version='auto',
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",  # Use the Docker socket
    network_mode="host",
    dag = scrapy_dag
)

wait_container = PythonOperator(
    task_id = 'Waiting_for_janusgraph',
    python_callable=lambda: check_container(),
    dag = scrapy_dag
)

#Post scrape SQL/gremlin python. Streamlit access point for specific data time.
postscrape_script = BashOperator(
    task_id='Post-Scrape_script',
    bash_command = (
        'echo "Running post-scrape script" && '
        'ssh -i /opt/airflow/dags/id_rsa_airflow ec2-user@3.22.55.181 "python3 /home/ec2-user/post_scrape.py"'
    ),
    dag = scrapy_dag
)
#JANUSGRAPH AND STREAMLIT WILL BE TURNED ON MANUALLY FOR QUERIES.
janusgraph_container >> add_known_host >> prescrape_script >> scrapy_container >> wait_container >> postscrape_script