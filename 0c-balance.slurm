#!/bin/bash

#SBATCH --job-name=balance_job
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=2:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage data in 
LOCAL_DATA="/tmp/${USER}_${SLURM_JOB_ID}/data"
LOCAL_CONFIG="/tmp/${USER}_${SLURM_JOB_ID}/config"
mkdir -p "$LOCAL_DATA" "$LOCAL_CONFIG"

# config/balance.json
cp /gscratch/stf/$USER/thesis/config/preprocess/balance.json "$LOCAL_CONFIG"/

# output/preprocess/manifest
cp /gscratch/stf/$USER/thesis/output/preprocess/manifest.json "$LOCAL_DATA"/

# leu_data and metadata_source
cp /gscratch/stf/$USER/thesis/output/preprocess/leu_data.jsonl.gz "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/output/preprocess/metadata_enriched.jsonl.gz "$LOCAL_DATA"/

# Run balanced strat
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m preprocess.balance \
    --config_path "$LOCAL_CONFIG"/balance.json \
    --leu_data "$LOCAL_DATA"/leu_data.jsonl.gz \
    --metadata_enriched "$LOCAL_DATA"/metadata_enriched.jsonl.gz \
    --output_dir "$LOCAL_DATA" \
    --strategy balanced

# Run full strat
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m preprocess.balance \
    --config_path "$LOCAL_CONFIG"/balance.json \
    --leu_data "$LOCAL_DATA"/leu_data.jsonl.gz \
    --metdata_enriched "$LOCAL_DATA"/metadata_enriched.jsonl.gz \
    --output_dir "$LOCAL_DATA" \
    --strategy full

# Stage data out
BALANCED_DIR="/gscratch/stf/$USER/thesis/output/preprocess/balanced"
FULL_DIR="/gscratch/stf/$USER/thesis/output/preprocess/full"

mkdir -p "$BALANCED_DIR" "$FULL_DIR"
cp "$LOCAL_DATA"/manifest.json /gscratch/stf/$USER/thesis/output/preprocess/
cp -r "$LOCAL_DATA"/balanced/* $BALANCED_DIR
cp -r "$LOCAL_DATA"/full/* $FULL_DIR