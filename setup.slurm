#!/bin/bash

#SBATCH --job-name=setup_job
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=16G
#SBATCH --time=4:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=jcmw614@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# command:
echo "Loading module..."
module load conda
echo "Module loaded, creating env"
conda create --name thesis-env python=3.12
echo "Activating env..."
conda activate thesis-env
echo "Installing OpenMP..."
conda install -c conda-forge llvm-openmp
echo "Installing requirements..."
pip install -r requirements.txt
echo "Installing dolma as pipx dep..."
pipx install dolma
echo "Setting pipx path"
pipx ensurepath
