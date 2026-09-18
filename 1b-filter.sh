#!/bin/bash

# Exit on error
set -e

CONDA_PYTHON="${CONDA_PYTHON:-python}" # CONDA_PYTHON should only be set on Hyak
CONFIG="config/filter/pipeline.json"
JOB_NAME="fineweb_filter" # must match job name passed to datatrove pipeline
POLL_INTERVAL=30 # Seconds between checks
SHARD_DIR="output/preprocess/shards"
SHARD_JOB_NAME="shard_leu"

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

if [ ! -d "$SHARD_DIR" ] || [ -z "$(ls -A "$SHARD_DIR" 2>/dev/null)" ]; then
    echo "No shards found — splitting $INPUT_FILE..."

    SHARD_JOB_ID=$(sbatch --parsable 1a-shard.slurm)
    echo "Waiting for job $SHARD_JOB_ID ('$SHARD_JOB_NAME') to finish..."

    while squeue -j "$SHARD_JOB_ID" -h 2>/dev/null | grep -q .; do
        sleep "$POLL_INTERVAL"
    done

    SHARD_FAILED=$(sacct -j "$SHARD_JOB_ID" -n --format=JobName,State,ExitCode 2>/dev/null | \
        grep -v "COMPLETED" || true)

    if [ -n "$SHARD_FAILED" ]; then
        echo "Error: job $SHARD_JOB_ID ('$SHARD_JOB_NAME') did not complete successfully:"
        echo "$SHARD_FAILED"
        exit 1
    fi

    if [ -z "$(ls -A "$SHARD_DIR" 2>/dev/null)" ]; then
        echo "Error: shard_input reported success but $SHARD_DIR is still empty."
        exit 1
    fi
    echo "Sharding complete."
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

PIPELINE_JOB_ID=$(cat job_ids.txt)
echo "Waiting for the'$PIPELINE_JOB_ID' batch to finish..."

while squeue -j "$PIPELINE_JOB_ID" -h | grep -q .; do
    sleep "$POLL_INTERVAL"
done

FAILED_JOBS=$(sacct -j "$PIPELINE_JOB_ID" -n --format=State,ExitCode | grep -v "COMPLETED")
if [ -n "$FAILED_JOBS" ]; then
    echo "Error: one or more jobs named '$JOB_NAME' did not complete successfully:"
    echo "$FAILED_JOBS"
    exit 1
fi

if [ ! -f "${LOG_PATH}/stats.json" ]; then
    echo "Error: stats.json not found even though jobs reported COMPLETED."
    exit 1
fi

echo "Collecting stats..."
sbatch 1c-audit.slurm
