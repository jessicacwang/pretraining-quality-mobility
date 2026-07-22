#!/bin/bash

#SBATCH --job-name=setup_job
#SBATCH --account=stf
#SBATCH --partition=compute-hugemem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=4:00:00
#SBATCH -o log/%x_%j.out
#SBATCH --mail-user=%u@uw.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# command:
echo "Loading module..."
module load conda

echo "Activating env..."
conda activate /gscratch/stf/$USER/conda/envs/thesis-env/

echo "Installing OpenMP..."
conda install -c conda-forge llvm-openmp

echo "Installing requirements..."
pip install -r requirements.txt

echo "Installing dolma as pipx dep..."
pipx install dolma

echo "Setting pipx path"
pipx ensurepath
