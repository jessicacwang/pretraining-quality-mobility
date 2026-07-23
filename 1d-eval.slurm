#!/bin/bash

#SBATCH --job-name=filter_eval
#SBATCH --account=stf
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4G
#SBATCH --time=20:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# Stage in data
LOCAL_DATA="/tmp/${USER}_${SLURM_JOB_ID}/data"
mkdir -p "$LOCAL_DATA"

cp /gscratch/stf/$USER/thesis/output/filter/*.jsonl.gz "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/output/filter/audit/manifest.json "$LOCAL_DATA"/
cp /gscratch/stf/$USER/thesis/output/preprocess/metadata_source.jsonl.gz "$LOCAL_DATA"/

echo "Correlating CMI with filter exclusion..."
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.correlation \
    --metadata_source "$LOCAL_DATA"/metadata_source.jsonl.gz \
    --audit_dir "$LOCAL_DATA"/

echo "Computing PMI between cluster, source, component, genre and exclusion..."
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.pmi \
    --output_dir "$LOCAL_DATA"/pmi --audit_dir "$LOCAL_DATA"/

echo "Retention sanity check below:"
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m eval.retention \
    --output_dir "$LOCAL_DATA"/retention --audit_dir "$LOCAL_DATA"/

# Stage out data
mkdir -p /gscratch/stf/$USER/thesis/output/eval/pmi /gscratch/stf/$USER/thesis/output/eval/retention
cp "$LOCAL_DATA"/pmi/*.csv /gscratch/stf/$USER/thesis/output/eval/pmi/
cp "$LOCAL_DATA"/retention/* /gscratch/stf/$USER/thesis/output/eval/retention/