#!/bin/bash

#SBATCH --job-name=unify_job
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=2:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage input files on node scratch
LOCAL_DATA="/tmp/${USER}_${SLURM_JOB_ID}/data"
LOCAL_CONFIG="/tmp/${USER}_${SLURM_JOB_ID}/config"
LOCAL_OUTPUT="/tmp/${USER}_${SLURM_JOB_ID}/output"
mkdir -p "$LOCAL_CONFIG" "$LOCAL_OUTPUT" "$LOCAL_DATA" 
mkdir -p "$LOCAL_DATA"/ice "$LOCAL_DATA"/glowbe-text

echo "Staging data in working node..."
# config/preprocess/unify.json
cp /gscratch/stf/$USER/thesis/config/preprocess/unify.json "$LOCAL_CONFIG"/
echo "Config staged"

# output/preprocess/manifest
cp /gscratch/stf/$USER/thesis/output/preprocess/manifest.json "$LOCAL_DATA"/
echo "Manifest staged"

# source courpura
cp -r /gscratch/stf/$USER/data/ice/*  "$LOCAL_DATA"/ice
cp -r /gscratch/stf/$USER/data/glowbe/glowbe-text/* "$LOCAL_DATA"/glowbe-text

echo "Source data staged, unifying data sources..."

/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m preprocess.unify \
    --config_path "$LOCAL_CONFIG"/unify.json \
    --data_path "$LOCAL_DATA" \
    --output_dir "$LOCAL_OUTPUT" 
echo "Unification complete, staging data out..."

# Stage out data
cp "$LOCAL_DATA"/manifest.json /gscratch/stf/$USER/thesis/output/preprocess/
cp "$LOCAL_OUTPUT"/leu_data.jsonl.gz /gscratch/stf/$USER/thesis/output/preprocess/leu_data.jsonl.gz
echo "Step 0a complete"
