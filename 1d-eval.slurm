#!/bin/bash

#SBATCH --job-name=filter_eval
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=6G
#SBATCH --time=1:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage in data
LOCAL_DATA="/tmp/$SLURM_JOB_ID_data"
cp /gscratch/stf/$USER/thesis/output/filter/*.jsonl.gz "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/output/filter/audit/manifest.json "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/output/preprocess/metadata_source.jsonl.gz "$LOCAL_DATA"/

echo "Correlating CMI with filter exclusion..."
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.correlation \
    --metadata_source "$LOCAL_DATA"/metadata_source.jsonl.gz \
    --output_dir "$LOCAL_DATA"/

echo "Computing PMI between cluster, source, component, genre and exclusion..."
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.pmi \
    --output_dir "$LOCAL_DATA"/

echo "Retention sanity check below:"
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.retention \
    --output_dir "$LOCAL_DATA"/