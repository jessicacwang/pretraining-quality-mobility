#!/bin/bash

#SBATCH --job-name=filter_audit
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=12G
#SBATCH --time=2:00:00
#SBATCH -o log/%x_%j.out

# command:
/gscratch/stf/jcmw614/conda/envs/thesis-env/bin/python -m filter.audit
