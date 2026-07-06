#!/bin/bash
set -euo pipefail

POOL_NAME="${PREFECT_WORK_POOL:-trackflow-docker-pool}"
WORKER_TYPE="${PREFECT_WORKER_TYPE:-docker}"

echo "Starting Prefect ${WORKER_TYPE} worker for pool: ${POOL_NAME}"
exec prefect worker start --pool "${POOL_NAME}" --type "${WORKER_TYPE}"
