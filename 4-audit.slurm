#!/bin/bash

#SBATCH --job-name=filter_audit
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=6G
#SBATCH --time=1:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage in data files to node scratch
LOCAL_CONFIG="/tmp/${USER}_${SLURM_JOB_ID}/config"
LOCAL_OUTPUT="/tmp/${USER}_${SLURM_JOB_ID}/data"

mkdir -p "$LOCAL_OUTPUT" "$LOCAL_CONFIG"
cp -r /gscratch/stf/$USER/thesis/output/filter/* "$LOCAL_OUTPUT"/
cp /gscratch/stf/$USER/thesis/config/filter/pipeline.json "$LOCAL_CONFIG"/
cp /gscratch/stf/$USER/thesis/log/filter/stats.json "$LOCAL_OUTPUT"/

# Execute package
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m filter.audit \
    --output_dir "$LOCAL_OUTPUT" --config_path "$LOCAL_CONFIG"/pipeline.json

# Stage out new manifest
mkdir -p /gscratch/stf/$USER/thesis/output/filter/audit
cp "$LOCAL_OUTPUT"/audit/manifest.json /gscratch/stf/$USER/thesis/output/filter/audit/
