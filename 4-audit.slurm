#!/bin/bash

#SBATCH --job-name=filter_audit
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=16G
#SBATCH --time=8:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage in data files to node scratch
LOCAL_CONFIG="/tmp/$USER_$SLURM_JOB_ID/config"
LOCAL_DATA="/tmp/$USER_$SLURM_JOB_ID/data"

mkdir -p "$LOCAL_DATA" "$LOCAL_CONFIG"
cp -r /gscratch/stf/$USER/thesis/output/filter/* "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/config/* "$LOCAL_CONFIG"/

# Execute package
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m filter.audit \
    --output_dir "$LOCAL_DATA" --config_path "$LOCAL_CONFIG"/filter/pipeline.json

# Stage out new manifest
mkdir -p /gscratch/stf/$USER/thesis/output/filter/audit
cp "$LOCAL_DATA"/audit/manifest.json /gscratch/stf/$USER/thesis/output/filter/audit/
