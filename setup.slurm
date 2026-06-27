#!/bin/bash

#SBATCH --job-name=setup_job
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=5G
#SBATCH --time=10:00
#SBATCH -o log/%x_%j.out


# command:
module load conda
conda create --name thesis-env python=3.12
conda activate
pip install -r requirements.txt