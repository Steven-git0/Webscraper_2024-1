#!/bin/bash

# Add the airflow user to the docker group
groupadd -g 999 docker
usermod -aG docker ${AIRFLOW_UID:-50000}

# Start the original entrypoint script
exec /entrypoint "$@"
