#!/bin/bash

#SBATCH --job-name=enrich_job
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=2:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# TODO: stage input files on node scratch
/gscratch/stf/$USER/conda/envs/thesis-env/bin/python -m preprocess.enrich
