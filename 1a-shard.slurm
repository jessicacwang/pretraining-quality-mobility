#!/bin/bash
#SBATCH --job-name=shard_leu
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --cpus-per-task=8
#SBATCH --mem=4G
#SBATCH --time=1:00:00
#SBATCH --chdir=/gscratch/stf/jcmw614/thesis
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

set -e
mkdir -p output/preprocess/shards
zcat output/preprocess/leu_data.jsonl.gz | split -l 50000 - output/preprocess/shards/shard_
ls output/preprocess/shards/shard_* | xargs -P 8 -n 1 gzip
