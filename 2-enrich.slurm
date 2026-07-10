#!/bin/bash

#SBATCH --job-name=enrich_job
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=1:00:00
#SBATCH -o log/%x_%j.out


# command:
/gscratch/scrubbed/jcmw614/conda/envs/thesis-env/bin/python -m preprocess.enrich