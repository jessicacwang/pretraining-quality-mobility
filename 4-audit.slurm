#!/bin/bash

#SBATCH --job-name=filter_audit
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=16G
#SBATCH --time=8:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# command:
/gscratch/stf/jcmw614/conda/envs/thesis-env/bin/python -m filter.audit
