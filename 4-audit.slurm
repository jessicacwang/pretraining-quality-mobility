#!/bin/bash

#SBATCH --job-name=filter_audit
#SBATCH --account=stf
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=16G
#SBATCH --time=4:00:00
#SBATCH -o log/%x_%j.out

# command:
/gscratch/stf/jcmw614/conda/envs/thesis-env/bin/python -m filter.audit
