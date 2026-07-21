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

# command:
/gscratch/stf/jcmw614/conda/envs/thesis-env/bin/python -m preprocess.unify
