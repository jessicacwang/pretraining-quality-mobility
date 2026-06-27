#!/bin/bash

#SBATCH --job-name=unify_job
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=5G
#SBATCH --time=1:00:00
#SBATCH -o log/%x_%j.out


# command:
/gscratch/scrubbed/jcmw614/conda/envs/thesis-env/bin/python -m preprocess.unify