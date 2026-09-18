#!/bin/bash

#SBATCH --job-name=enrich_job
#SBATCH --account=stf
#SBATCH --partition=ckpt-all
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=4:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage input files on node scratch
LOCAL_DATA="/tmp/${USER}_${SLURM_JOB_ID}/data"
LOCAL_CONFIG="/tmp/${USER}_${SLURM_JOB_ID}/config"
mkdir -p "$LOCAL_DATA" "$LOCAL_CONFIG"

echo "Staging data in working node..."
# config/enrich.json
cp /gscratch/stf/$USER/thesis/config/preprocess/enrich.json "$LOCAL_CONFIG"/
echo "Config staged"

# output/preprocess/manifest
cp /gscratch/stf/$USER/thesis/output/preprocess/manifest.json "$LOCAL_DATA"/
echo "Manifest staged"

# leu_data and metadata_source
cp /gscratch/stf/$USER/thesis/output/preprocess/leu_data.jsonl.gz "$LOCAL_DATA"
cp /gscratch/stf/$USER/thesis/output/preprocess/metadata_source.jsonl.gz "$LOCAL_DATA"
echo "Source data staged, running metadata enrichment..."

# Run
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m preprocess.enrich \
    --config_path "$LOCAL_CONFIG"/enrich.json \
    --output_dir "$LOCAL_DATA" \
    --leu_data "$LOCAL_DATA"/leu_data.jsonl.gz \
    --metadata_source "$LOCAL_DATA"/metadata_source.jsonl.gz
echo "Enrichment complete, staging data out..."

# Stage out
cp "$LOCAL_DATA"/manifest.json /gscratch/stf/$USER/thesis/output/preprocess/
cp "$LOCAL_DATA"/metadata_enriched.jsonl.gz /gscratch/stf/$USER/thesis/output/preprocess/
echo "Step 0b complete"