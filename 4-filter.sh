#!/bin/bash

# Exit on error
set -e

CONDA_PYTHON="${CONDA_PYTHON:-python}" # CONDA_PYTHON should only be set on Hyak
CONFIG="config/filter/pipeline.json"
JOB_NAME="fineweb_filter" # must match job name passed to datatrove pipeline
POLL_INTERVAL=30 # Seconds between checks

# ============ Parse args ============
EXECUTOR_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --executor)
            EXECUTOR_OVERRIDE="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# ========== Split leu_data into shard if not already done ===========
SHARD_DIR="output/preprocess/shards"
if [ ! -d "$SHARD_DIR" ] || [ -z "$(ls -A "$SHARD_DIR" 2>/dev/null)" ]; then
    echo "No shards found — splitting $INPUT_FILE..."
    mkdir -p "$SHARD_DIR"
    if [ "$EXECUTOR_OVERRIDE" == "local" ]; then
        INPUT_FILE=$("$CONDA_PYTHON" -c "import json; print(json.load(open('$CONFIG'))['toy_data'])")
        gunzip -c "$INPUT_FILE" | split -l 2500 - "${SHARD_DIR}/shard_"
    else
        INPUT_FILE=$("$CONDA_PYTHON" -c "import json; print(json.load(open('$CONFIG'))['leu_data'])")
        zcat "$INPUT_FILE" | split -l 50000 - "${SHARD_DIR}/shard_"
    fi
    for f in "${SHARD_DIR}"/shard_*; do gzip "$f"; done
else
    echo "Shards already exist in $SHARD_DIR — skipping split."
fi

# ============ Resolve config values ============
if [ -n "$EXECUTOR_OVERRIDE" ]; then
    EXECUTOR="$EXECUTOR_OVERRIDE"
else
    EXECUTOR="slurm"
fi

LOG_PATH=$("$CONDA_PYTHON" -c "import json; print(json.load(open('$CONFIG'))['$EXECUTOR']['log_dir'])")

echo "Using executor: $EXECUTOR"

# ============ Local path ============
if [ "$EXECUTOR" == "local" ]; then
    echo "Running locally (LocalPipelineExecutor)..."
    "$CONDA_PYTHON" -m filter.pipeline --executor local

    if [ ! -f "${LOG_PATH}/stats.json" ]; then
        echo "Error: stats.json not found after local run."
        exit 1
    fi
    exit 0
fi

# ============ Slurm path ============
echo "Submitting datatrove pipeline..."
"$CONDA_PYTHON" -m filter.pipeline --executor slurm

echo "Waiting for Slurm jobs named '$JOB_NAME' to finish..."
while squeue -u "$USER" -n "$JOB_NAME" -h | grep -q .; do
    sleep "$POLL_INTERVAL"
done

FAILED_JOBS=$(sacct -u "$USER" -n --format=JobID,JobName%30,State,ExitCode \
    | awk -v job="$JOB_NAME" '$2 == job && $3 !~ /COMPLETED/ {print}')
if [ -n "$FAILED_JOBS" ]; then
    echo "Error: one or more jobs named '$JOB_NAME' did not complete successfully:"
    echo "$FAILED_JOBS"
    exit 1
fi

if [ ! -f "${LOG_PATH}/stats.json" ]; then
    echo "Error: stats.json not found even though jobs reported COMPLETED."
    exit 1
fi
